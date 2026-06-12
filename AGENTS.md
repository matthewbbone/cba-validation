# Collective Bargaining Validation

This repo holds the code to validate the results of a project that uses LLMs to extract provisions from U.S. collective bargaining agreements (CBAs) and judge the generosity of provision bundles (e.g. healthcare, compensation, etc.). We have a collection of ~8,500 of these agreements in PDF format. They span from the 1950s to 2025 and include a wide array of industries and states. However, representation is best after 1995. 

We have four types of validation exercises that we aim to complete:
1. Stylized Facts: These are trends or characteristics of CBA content usually derived from qualitative literature. This could include trends like decreasing retiree healthcare coverage or compositional facts like public employers tend to have low wages but high quality benefits around leave and pensions. These stylized facts should be something we can observe just in the content of our CBA sample and do not require external data.
2. External Data: We use administrative data and surveys to ensure our extractions match what we would expect given external data. For instance, we compare extracted wages to union and non-union wage data from the current population survey. Additionally, we plan to get management survey data to compare management practices with management rights in the CBAs
3. Comparative Pipelines: We have an independently developed LLM pipeline with a different model (e.g. GPT vs Claude) and we want to make sure these two pipelines converge towards some true extractions/generosity scores, or at least be able to show that the main pipeline is better. 
4. Human Benchmark: We want to create a golden test set for both provision extraction and generosity scoring. To do this we need to create a web UI that (1) displays a CBA pdf and asks the user to extract particular information and (2) displays a bundle of provisions and asks the user to judge its generosity.

