## PR Compression Strategy

### Motivation
Pull Requests can be very long and contain a lot of information with varying degree of relevance to the pr-agent.
We want to be able to pack as much information as possible in a single LMM prompt, while keeping the information relevant to the pr-agent.

### Our Strategy
#### Repo language prioritization strategy
We prioritize the languages of the repo based on the following criteria:
1. Given the main languages used in the repo
2. We sort the PR files by the most common languages in the repo (in descending order): 
   * ```[[file.py, file2.py],[file3.js, file4.jsx],[readme.md]]```
3. Withing each language we sort the files by the number of tokens in the file (in descending order):
   * ```[[file2.py, file.py],[file4.jsx, file3.js],[readme.md]]```

#### PR compression strategy

####  Adaptive and token-aware file patch fitting:
 
