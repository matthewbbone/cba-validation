"""Offline unit tests for the CUAD clause-retrieval benchmark.

Run with::

    python -m unittest discover -s tests -p 'test_cuad_validation.py' -v

The tests deliberately use synthetic contracts and fake vectors. They never download
CUAD, load Chonkie recipes, or instantiate EmbeddingGemma.
"""

from __future__ import annotations

import csv
import json
import tempfile
import unittest
from types import SimpleNamespace

from pipeline.cuad_validation import evaluate_recall as recall
from pipeline.cuad_validation import prepare_cuad_data as data


class CuadParsingTests(unittest.TestCase):
    def test_parse_csv_list_accepts_only_a_list_of_strings(self) -> None:
        self.assertEqual(data.parse_csv_list("['alpha', 'beta']"), ("alpha", "beta"))
        self.assertEqual(data.parse_csv_list("[]"), ())

        for malformed in (
            "not a literal",
            "('tuple',)",
            "{'set'}",
            "[1]",
            "__import__('pathlib').Path('should-not-exist').touch()",
        ):
            with self.subTest(malformed=malformed):
                with self.assertRaises(data.CuadDataError):
                    data.parse_csv_list(malformed)

        with self.assertRaises(data.CuadDataError):
            data.parse_csv_list(None)  # type: ignore[arg-type]

    def test_normalized_join_keys_handle_pdf_suffix_and_reject_collisions(self) -> None:
        expected = "acmecoagreement2020"
        self.assertEqual(data.normalize_key("Acme Co - Agreement (2020).PDF'"), expected)
        self.assertEqual(data.normalize_key(" acme_co_agreement_2020 "), expected)

        with self.assertRaisesRegex(data.CuadDataError, "collision"):
            data._unique_index(  # noqa: SLF001 - collision validation is intentional API coverage
                ["Acme Co - Agreement (2020).PDF", "acme_co_agreement_2020"],
                kind="contract",
            )
        with self.assertRaisesRegex(data.CuadDataError, "normalizes to empty"):
            data.normalize_key(" -- '")

    def test_split_provision_drops_empty_and_duplicate_omitted_pieces(self) -> None:
        self.assertEqual(
            data.split_provision(" alpha <omitted> beta <omitted> alpha <omitted> "),
            ("alpha", "beta"),
        )
        self.assertEqual(data.split_provision(""), ())
        with self.assertRaises(data.CuadDataError):
            data.split_provision(3)  # type: ignore[arg-type]


class GoldAlignmentTests(unittest.TestCase):
    def test_segments_map_only_to_exact_authoritative_offsets(self) -> None:
        context = "prefix alpha middle beta suffix"
        answers = [
            {"text": "alpha", "answer_start": 7},
            {"text": "beta", "answer_start": 20},
        ]

        segments = data.align_gold_segments(context, ("beta", "alpha", "beta"), answers)

        self.assertEqual(
            segments,
            (
                data.GoldSegment("beta", 20, 24),
                data.GoldSegment("alpha", 7, 12),
            ),
        )

    def test_alignment_rejects_unmatched_invalid_and_ambiguous_answers(self) -> None:
        with self.assertRaisesRegex(data.CuadDataError, "no exact JSON answer"):
            data.align_gold_segments("alpha", ("beta",), [{"text": "alpha", "answer_start": 0}])

        with self.assertRaisesRegex(data.CuadDataError, "does not exactly slice"):
            data.align_gold_segments("alpha", ("alpha",), [{"text": "alpha", "answer_start": 1}])

        context = "alpha then alpha"
        with self.assertRaisesRegex(data.CuadDataError, "ambiguous offsets"):
            data.align_gold_segments(
                context,
                ("alpha",),
                [
                    {"text": "alpha", "answer_start": 0},
                    {"text": "alpha", "answer_start": 11},
                ],
            )

    def test_duplicate_span_references_are_not_duplicate_unique_gold_segments(self) -> None:
        segment = data.GoldSegment("alpha", 0, 5)
        provisions = tuple(
            data.Provision(
                provision_id=f"c::kind::{index}",
                category_id="kind",
                category_label="Kind",
                provision_index=index,
                text="alpha",
                segments=(segment,),
            )
            for index in range(2)
        )
        corpus = data.CuadCorpus(
            contracts=(data.Contract("c", "alpha", provisions),),
            categories=(data.Category("kind", "Kind", "Description", "Kind. Description"),),
        )

        self.assertEqual(corpus.provision_count, 2)
        self.assertEqual(corpus.segment_reference_count, 2)
        self.assertEqual(corpus.gold_segment_count, 1)


class ChunkOffsetTests(unittest.TestCase):
    def test_exact_and_nearby_offsets_are_aligned_to_source(self) -> None:
        source = "0123456789"
        self.assertEqual(recall.align_chunk_offset(source, "345", 3, 6), (3, 6))
        self.assertEqual(recall.align_chunk_offset(source, "345", 2, 5, window=2), (3, 6))
        self.assertEqual(recall.align_chunk_offset(source, "345", 1, 4, window=2), (3, 6))

    def test_unresolved_and_out_of_order_chunks_fail(self) -> None:
        with self.assertRaises(recall.OffsetAlignmentError):
            recall.align_chunk_offset("alpha beta", "missing", 0, 7, window=2)

        chunks = [
            SimpleNamespace(text="beta", start_index=6, end_index=10),
            SimpleNamespace(text="alpha", start_index=0, end_index=5),
        ]
        with self.assertRaisesRegex(recall.OffsetAlignmentError, "chunk 1"):
            recall.realign_chunk_offsets("alpha beta", chunks, window=2)

    def test_chunk_contract_realigns_and_retains_only_exact_nonblank_slices(self) -> None:
        source = "alpha  beta"
        raw_chunks = [
            SimpleNamespace(text="alpha", start_index=1, end_index=6, token_count=1),
            SimpleNamespace(text="  ", start_index=5, end_index=7, token_count=0),
            SimpleNamespace(text="beta", start_index=7, end_index=11, token_count=1),
        ]

        chunks, stats = recall.chunk_contract(source, lambda _: raw_chunks, alignment_window=2)

        self.assertEqual([chunk["chunk_id"] for chunk in chunks], [0, 1])
        self.assertEqual(
            [(chunk["char_start"], chunk["char_end"], chunk["text"]) for chunk in chunks],
            [(0, 5, "alpha"), (7, 11, "beta")],
        )
        self.assertTrue(all(source[c["char_start"] : c["char_end"]] == c["text"] for c in chunks))
        self.assertEqual(stats["n_offset_corrections"], 1)
        self.assertEqual(stats["n_blank_skipped"], 1)


class RankingAndIntervalTests(unittest.TestCase):
    def test_ranking_uses_rounded_scores_then_numeric_chunk_id(self) -> None:
        ranked = recall.rank_chunks(
            [0.55554, 0.55553, 0.9],
            decimals=4,
            chunk_ids=["10", "2", "3"],
        )
        self.assertEqual(ranked, ["3", "2", "10"])

        with self.assertRaisesRegex(ValueError, "numerically unique"):
            recall.rank_chunks([0.1, 0.2], chunk_ids=[2, "2"])

    def test_cutoffs_use_ceil_and_keep_one_chunk_for_short_documents(self) -> None:
        self.assertEqual(recall.cutoff_count(0, 0.01), 0)
        self.assertEqual(recall.cutoff_count(1, 0.01), 1)
        self.assertEqual(recall.cutoff_count(3, 0.01), 1)
        self.assertEqual(recall.cutoff_count(20, 0.05), 1)
        self.assertEqual(recall.cutoff_count(21, 0.05), 2)
        self.assertEqual(recall.cutoff_count(101, 0.01), 2)

    def test_interval_union_intersection_and_half_open_boundaries(self) -> None:
        intervals = [(8, 12), (0, 3), (3, 5), (7, 10), (4, 4)]
        self.assertEqual(recall.merge_intervals(intervals), [(0, 5), (7, 12)])
        self.assertEqual(recall.interval_union_length(intervals), 10)
        self.assertEqual(
            recall.interval_intersection_length([(0, 3), (7, 10)], [(2, 8)]),
            2,
        )
        self.assertAlmostEqual(recall.interval_coverage([(0, 3), (7, 10)], [(2, 8)]), 1 / 3)
        self.assertFalse(recall.intervals_overlap((0, 5), (5, 9)))
        self.assertTrue(recall.intervals_overlap((0, 5), (4, 9)))

    def test_provision_metrics_distinguish_any_majority_and_full_coverage(self) -> None:
        chunks = [
            {"chunk_id": 0, "char_start": 9, "char_end": 10},
            {"chunk_id": 1, "char_start": 0, "char_end": 9},
            {"chunk_id": 2, "char_start": 20, "char_end": 25},
            {"chunk_id": 3, "char_start": 25, "char_end": 30},
        ]
        cutoffs = (("one", 0.25), ("two", 0.5), ("three", 0.75), ("four", 1.0))

        result = recall.provision_metrics(
            [(0, 10), (20, 30)], chunks, [0, 1, 2, 3], cutoffs=cutoffs
        )

        self.assertEqual(result["gold_char_count"], 20)
        self.assertEqual(result["cutoffs"]["one"]["covered_gold_chars"], 1)
        self.assertTrue(result["cutoffs"]["one"]["recalled"])
        self.assertFalse(result["cutoffs"]["one"]["majority"])
        self.assertTrue(result["cutoffs"]["two"]["majority"])
        self.assertFalse(result["cutoffs"]["two"]["full"])
        self.assertTrue(result["cutoffs"]["four"]["full"])
        coverages = [result["cutoffs"][name]["coverage"] for name, _ in cutoffs]
        self.assertEqual(coverages, sorted(coverages))


class SyntheticEvaluationTests(unittest.TestCase):
    @staticmethod
    def _fixture() -> tuple[
        str,
        data.Contract,
        tuple[data.Category, ...],
        list[SimpleNamespace],
        list[list[float]],
    ]:
        source = "AAAA BBBB CCCC DDDD"
        categories = (
            data.Category("leave", "Leave", "Paid time away", "Leave. Paid time away"),
            data.Category("pay", "Pay", "Cash compensation", "Pay. Cash compensation"),
        )
        provisions = (
            data.Provision(
                "contract::leave::0",
                "leave",
                "Leave",
                0,
                "BBBB",
                (data.GoldSegment("BBBB", 5, 9),),
            ),
            data.Provision(
                "contract::pay::0",
                "pay",
                "Pay",
                0,
                "DDDD",
                (data.GoldSegment("DDDD", 15, 19),),
            ),
        )
        contract = data.Contract("contract", source, provisions)
        raw_chunks = [
            SimpleNamespace(text="AAAA", start_index=0, end_index=4, token_count=1),
            SimpleNamespace(text="BBBB", start_index=5, end_index=9, token_count=1),
            SimpleNamespace(text="CCCC", start_index=10, end_index=14, token_count=1),
            SimpleNamespace(text="DDDD", start_index=15, end_index=19, token_count=1),
        ]
        # Rows are chunks; columns are (leave, pay). Leave's gold chunk ranks second,
        # while pay's gold chunk ranks first.
        scores = [
            [0.90004, 0.1],
            [0.80004, 0.2],
            [0.70004, 0.3],
            [0.60004, 0.9],
        ]
        return source, contract, categories, raw_chunks, scores

    def test_offline_chunk_evaluate_aggregate_and_write(self) -> None:
        source, contract, categories, raw_chunks, scores = self._fixture()
        chunks, _ = recall.chunk_contract(source, lambda _: raw_chunks)
        detail = recall.evaluate_contract(contract, categories, chunks, scores)
        headline, per_category = recall.aggregate_evaluation(detail, categories)

        self.assertEqual(len(detail), 2)
        self.assertEqual(headline["denominator"], 2)
        self.assertEqual(
            headline["cutoffs"]["top_1_percent"]["any_overlap"]["numerator"], 1
        )
        self.assertEqual(
            headline["cutoffs"]["top_1_percent"]["any_overlap"]["percent"], 50.0
        )
        self.assertEqual(
            headline["cutoffs"]["top_50_percent"]["any_overlap"]["numerator"], 2
        )
        self.assertEqual(
            headline["cutoffs"]["top_50_percent"]["any_overlap"]["percent"], 100.0
        )
        numerators = [
            headline["cutoffs"][name]["any_overlap"]["numerator"]
            for name, _ in recall.CUTOFFS
        ]
        self.assertEqual(numerators, sorted(numerators))
        self.assertEqual({row["category_id"] for row in per_category}, {"leave", "pay"})

        summary = {
            "schema_version": recall.SCHEMA_VERSION,
            "headline": headline,
            "corpus": {"provisions": 2},
        }
        with tempfile.TemporaryDirectory() as temporary:
            paths = recall.write_results(temporary, summary, per_category, detail)
            self.assertTrue(all(path.is_file() for path in paths))
            self.assertEqual(json.loads(paths[0].read_text(encoding="utf-8")), summary)
            with paths[1].open(encoding="utf-8", newline="") as handle:
                category_rows = list(csv.DictReader(handle))
            self.assertEqual(len(category_rows), 2)
            provision_rows = [
                json.loads(line) for line in paths[2].read_text(encoding="utf-8").splitlines()
            ]
            self.assertEqual(len(provision_rows), 2)
            self.assertEqual(
                {row["provision_id"] for row in provision_rows},
                {"contract::leave::0", "contract::pay::0"},
            )

    def test_micro_aggregation_rejects_nonmonotonic_detail_rows(self) -> None:
        _, _, categories, _, _ = self._fixture()
        cutoff_rows = {}
        for index, (name, fraction) in enumerate(recall.CUTOFFS):
            cutoff_rows[name] = {
                "fraction": fraction,
                "recalled": index != 1,
                "majority": False,
                "full": False,
            }
        bad_detail = [{"category_id": "leave", "cutoffs": cutoff_rows}]
        with self.assertRaisesRegex(AssertionError, "not monotonic"):
            recall.aggregate_evaluation(bad_detail, categories)

    def test_score_matrix_shape_is_enforced(self) -> None:
        source, contract, categories, raw_chunks, _ = self._fixture()
        chunks, _ = recall.chunk_contract(source, lambda _: raw_chunks)
        with self.assertRaisesRegex(ValueError, "score matrix has shape"):
            recall.evaluate_contract(contract, categories, chunks, [[0.1]] * len(chunks))


if __name__ == "__main__":
    unittest.main()
