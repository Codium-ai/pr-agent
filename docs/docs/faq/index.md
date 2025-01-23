# FAQ

??? note "Q: Can Qodo Merge serve as a substitute for a human reviewer?"
    #### Answer:<span style="display:none;">1</span>

    Qodo Merge is designed to assist, not replace, human reviewers.

    Reviewing PRs is a tedious and time-consuming task often seen as a "chore". In addition, the longer the PR – the shorter the relative feedback, since long PRs can overwhelm reviewers, both in terms of technical difficulty, and the actual review time.
    Qodo Merge aims to address these pain points, and to assist and empower both the PR author and reviewer.

    However, Qodo Merge has built-in safeguards to ensure the developer remains in the driver's seat. For example:

    1. Preserves user's original PR header
    2. Places user's description above the AI-generated PR description
    3. Won't approve PRs; approval remains reviewer's responsibility
    4. The code suggestions are optional, and aim to:
        - Encourage self-review and self-reflection
        - Highlight potential bugs or oversights
        - Enhance code quality and promote best practices

    Read more about this issue in our [blog](https://www.codium.ai/blog/understanding-the-challenges-and-pain-points-of-the-pull-request-cycle/)

___

??? note "Q: I received an incorrect or irrelevant suggestion. Why?"

    #### Answer:<span style="display:none;">2</span>

    - Modern AI models, like Claude 3.5 Sonnet and GPT-4, are improving rapidly but remain imperfect. Users should critically evaluate all suggestions rather than accepting them automatically.
    - AI errors are rare, but possible. A main value from reviewing the code suggestions lies in their high probability of catching **mistakes or bugs made by the PR author**. We believe it's worth spending 30-60 seconds reviewing suggestions, even if some aren't relevant, as this practice can enhance code quality and prevent bugs in production.


    - The hierarchical structure of the suggestions is designed to help the user _quickly_ understand them, and to decide which ones are relevant and which are not:

        - Only if the `Category` header is relevant, the user should move to the summarized suggestion description.
        - Only if the summarized suggestion description is relevant, the user should click on the collapsible, to read the full suggestion description with a code preview example.

    - In addition, we recommend to use the [`extra_instructions`](https://qodo-merge-docs.qodo.ai/tools/improve/#extra-instructions-and-best-practices) field to guide the model to suggestions that are more relevant to the specific needs of the project.
    - The interactive [PR chat](https://qodo-merge-docs.qodo.ai/chrome-extension/) also provides an easy way to get more tailored suggestions and feedback from the AI model.

___

??? note "Q: How can I get more tailored suggestions?"
    #### Answer:<span style="display:none;">3</span>

    See [here](https://qodo-merge-docs.qodo.ai/tools/improve/#extra-instructions-and-best-practices) for more information on how to use the `extra_instructions` and `best_practices` configuration options, to guide the model to more tailored suggestions.

___

??? note "Q: Will you store my code? Are you using my code to train models?"
    #### Answer:<span style="display:none;">4</span>

    No. Qodo Merge strict privacy policy ensures that your code is not stored or used for training purposes.

    For a detailed overview of our data privacy policy, please refer to [this link](https://qodo-merge-docs.qodo.ai/overview/data_privacy/)

___

??? note "Q: Can I use my own LLM keys with Qodo Merge?"
    #### Answer:<span style="display:none;">5</span>

    When you self-host the [open-source](https://github.com/Codium-ai/pr-agent) version, you use your own keys.

    Qodo Merge with SaaS deployment is a hosted version of Qodo Merge, where Qodo manages the infrastructure and the keys.
    For enterprise customers, on-prem deployment is also available. [Contact us](https://www.codium.ai/contact/#pricing) for more information.
___

??? note "Q: Can Qodo Merge review draft/offline PRs?"
    #### Answer:<span style="display:none;">5</span>

    Yes. While Qodo Merge won't automatically review draft PRs, you can still get feedback by manually requesting it through [online commenting](https://qodo-merge-docs.qodo.ai/usage-guide/automations_and_usage/#online-usage).

    For active PRs, you can customize the automatic feedback settings [here](https://qodo-merge-docs.qodo.ai/usage-guide/automations_and_usage/#qodo-merge-automatic-feedback) to match your team's workflow.
___

??? note "Q: Can the 'Review effort' feedback be calibrated or customized?"
    #### Answer:<span style="display:none;">5</span>

    Yes, you can customize review effort estimates using the `extra_instructions` configuration option (see [documentation](https://qodo-merge-docs.qodo.ai/tools/review/#configuration-options)).
    
    Example mapping:

    - Effort 1: < 30 minutes review time
    - Effort 2: 30-60 minutes review time
    - Effort 3: 60-90 minutes review time
    - ...
    
    Note: The effort levels (1-5) are primarily meant for _comparative_ purposes, helping teams prioritize reviewing smaller PRs first. The actual review duration may vary, as the focus is on providing consistent relative effort estimates.

___
