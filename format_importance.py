import numpy as np

from pr_agent.tools.pr_code_suggestions import PRCodeSuggestions

data = np.load('/Users/talrid/Git/pr-agent/data.npy', allow_pickle=True).tolist()
cls=PRCodeSuggestions(pr_url=None)
res = cls.generate_summarized_suggestions(data)
print(res)
