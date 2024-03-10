# To install:
pip install mkdocs
pip install mkdocs-material
pip install mkdocs-material-extensions
pip install "mkdocs-material[imaging]"

# docs
To run localy: `mkdocs serve`

To expand and customize the theme: [Material MKDocs](https://squidfunk.github.io/mkdocs-material/)

The deployment is managed on the gh-pages branches.
After each merge to main the deplloyment will be taken care of by GH action automatically and the new version will be available at: [Docs](https://codium-ai.github.io/docs/)

Github action is located in `.github/workflows/ci.yml` file.
