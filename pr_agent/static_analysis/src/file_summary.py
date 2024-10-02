import os
from pathlib import Path

from grep_ast import TreeContext
from grep_ast.parsers import PARSERS
# from pygments.lexers import guess_lexer_for_filename
# from pygments.token import Token
from tree_sitter_languages import get_language, get_parser


def filename_to_lang(filename):
    file_extension = os.path.splitext(filename)[1]
    lang = PARSERS.get(file_extension)
    return lang

class FileSummary:
    """
    This class is used to summarize the content of a file using tree-sitter queries.
    Supported languages: C, C++, C#, elisp, elixir, go, java, javascript, ocaml, php, python, ql, ruby, rust, typescript
    """
    def __init__(self, fname_full_path: str, project_base_path, parent_context=True, child_context=False, header_max=0):
        self.fname_full_path = fname_full_path
        self.project_base_path = project_base_path
        self.fname_rel = os.path.relpath(fname_full_path, project_base_path)
        self.main_queries_path = Path(__file__).parent.parent / 'queries'
        if not os.path.exists(fname_full_path):
            print(f"File {fname_full_path} does not exist")
        with open(fname_full_path, "r") as f:
            code = f.read()
        self.code = code.rstrip("\n") + "\n"
        self.parent_context = parent_context
        self.child_context = child_context
        self.header_max = header_max

    def summarize(self):
        query_results = self.get_query_results()
        summary_str = self.query_processing(query_results)
        return summary_str

    def render_file_summary(self, lines_of_interest: list):
        code = self.code
        fname_rel = self.fname_rel
        context = TreeContext(
            fname_rel,
            code,
            color=False,
            line_number=True,  # number the lines (1-indexed)
            parent_context=self.parent_context,
            child_context=self.child_context,
            last_line=False,
            margin=0,
            mark_lois=False,
            loi_pad=0,
            header_max=self.header_max,  # max number of lines to show in a function header
            show_top_of_file_parent_scope=False,
        )

        context.lines_of_interest = set()
        context.add_lines_of_interest(lines_of_interest)
        context.add_context()
        res = context.format()
        return res

    def query_processing(self, query_results: list):
        if not query_results:
            return ""

        output = ""
        def_lines = [q['line'] for q in query_results if q['kind'] == "def"]
        output += "\n"
        output += query_results[0]['fname'] + ":\n"
        output += self.render_file_summary(def_lines)
        return output

    def get_queries_scheme(self, lang) -> str:
        try:
            # Load the relevant queries
            path = os.path.join(self.main_queries_path, f"tree-sitter-{lang}-tags.scm")
            with open(path, "r") as f:
                return f.read()
        except KeyError:
            return ""

    def get_query_results(self):
        fname_rel = self.fname_rel
        code = self.code
        lang = filename_to_lang(fname_rel)
        if not lang:
            return

        try:
            language = get_language(lang)
            parser = get_parser(lang)
        except Exception as err:
            print(f"Skipping file {fname_rel}: {err}")
            return

        query_scheme_str = self.get_queries_scheme(lang)
        tree = parser.parse(bytes(code, "utf-8"))

        # Run the queries
        query = language.query(query_scheme_str)
        captures = list(query.captures(tree.root_node))

        # Parse the results into a list of "def" and "ref" tags
        visited_set = set()
        results = []
        for node, tag in captures:
            if tag.startswith("name.definition."):
                kind = "def"
            elif tag.startswith("name.reference."):
                kind = "ref"
            else:
                continue

            visited_set.add(kind)
            result = dict(
                fname=fname_rel,
                name=node.text.decode("utf-8"),
                kind=kind,
                line=node.start_point[0],
            )
            results.append(result)

        if "ref" in visited_set:
            return results
        if "def" not in visited_set:
            return results

        ## currently we are interested only in defs
        # # We saw defs, without any refs
        # # Some files only provide defs (cpp, for example)
        # # Use pygments to backfill refs
        # try:
        #     lexer = guess_lexer_for_filename(fname, code)
        # except Exception:
        #     return
        #
        # tokens = list(lexer.get_tokens(code))
        # tokens = [token[1] for token in tokens if token[0] in Token.Name]
        #
        # for t in tokens:
        #     result = dict(
        #         fname=fname,
        #         name=t,
        #         kind="ref",
        #         line=-1,
        #     )
        #     results.append(result)
        return results
