import os
from pathlib import Path

from pr_agent.static_analysis.src.file_summary import FileSummary


class TestFileSummary:
    def setup_method(self):
        self.base_path = Path(__file__).parent
        self.project_base_path = Path(__file__).parent.parent.parent.parent

    def test_file_summary_cpp(self):
        fname = os.path.join(self.base_path, 'example_files/AES.cpp')
        if not os.path.exists(fname):
            print(f"File {fname} does not exist")
            return False
        fname_summary = FileSummary(fname, self.project_base_path, parent_context=False, child_context=False,
                                    header_max=0)
        output = fname_summary.summarize()
        expected_output = '\npr_agent/static_analysis/tests/example_files/AES.cpp:\n...⋮...\n 32│namespace Common::AES\n 33│{\n...⋮...\n 36│template <Mode AesMode>\n 37│class ContextGeneric final : public Context\n 38│{\n 39│public:\n 40│  ContextGeneric(const u8* key)\n...⋮...\n 49│  virtual bool Crypt(const u8* iv, u8* iv_out, const u8* buf_in, u8* buf_out,\n...⋮...\n 70│#if defined(_M_X86_64)\n 71│\n...⋮...\n 84│template <Mode AesMode>\n 85│class ContextAESNI final : public Context\n 86│{\n 87│  static inline __m128i Aes128KeygenAssistFinish(__m128i key, __m128i kga)\n...⋮...\n103│  inline constexpr void StoreRoundKey(__m128i rk)\n...⋮...\n119│  inline constexpr __m128i Aes128Keygen(__m128i rk)\n...⋮...\n127│  ContextAESNI(const u8* key)\n...⋮...\n144│  inline void CryptBlock(__m128i* iv, const u8* buf_in, u8* buf_out) const\n...⋮...\n178│  inline void DecryptPipelined(__m128i* iv, const u8* buf_in, u8* buf_out) const\n...⋮...\n209│  virtual bool Crypt(const u8* iv, u8* iv_out, const u8* buf_in, u8* buf_out,\n...⋮...\n259│#if defined(_M_ARM_64)\n260│\n261│template <Mode AesMode>\n262│class ContextNeon final : public Context\n263│{\n264│public:\n265│  template <size_t RoundIdx>\n266│  inline constexpr void StoreRoundKey(const u32* rk)\n...⋮...\n281│  ContextNeon(const u8* key)\n...⋮...\n322│  inline void CryptBlock(uint8x16_t* iv, const u8* buf_in, u8* buf_out) const\n...⋮...\n353│  virtual bool Crypt(const u8* iv, u8* iv_out, const u8* buf_in, u8* buf_out,\n...⋮...\n381│template <Mode AesMode>\n382│std::unique_ptr<Context> CreateContext(const u8* key)\n...⋮...\n402│std::unique_ptr<Context> CreateContextEncrypt(const u8* key)\n...⋮...\n407│std::unique_ptr<Context> CreateContextDecrypt(const u8* key)\n...⋮...\n413│void CryptOFB(const u8* key, const u8* iv, u8* iv_out, const u8* buf_in, u8* buf_out, size_t size)\n...⋮...\n'
        assert output == expected_output

    def test_file_typescript(self):
        fname = os.path.join(self.base_path, 'example_files/match.ts')
        if not os.path.exists(fname):
            print(f"File {fname} does not exist")
            return False
        fname_summary = FileSummary(fname, self.project_base_path, parent_context=False, child_context=False,
                                    header_max=0)
        output = fname_summary.summarize()
        expected_output = '\npr_agent/static_analysis/tests/example_files/match.ts:\n...⋮...\n  6│type MatchState<output> =\n...⋮...\n 31│export function match<const input, output = symbols.unset>(\n...⋮...\n 46│class MatchExpression<input, output> {\n 47│  constructor(private input: input, private state: MatchState<output>) {}\n 48│\n 49│  with(...args: any[]): MatchExpression<input, output> {\n...⋮...\n 94│  when(\n...⋮...\n110│  otherwise(handler: (value: input) => output): output {\n...⋮...\n115│  exhaustive(): output {\n...⋮...\n119│  run(): output {\n...⋮...\n134│  returnType() {\n...⋮...\n'
        assert output == expected_output

    def test_file_java(self):
        fname = os.path.join(self.base_path, 'example_files/calc.java')
        if not os.path.exists(fname):
            print(f"File {fname} does not exist")
            return False
        fname_summary = FileSummary(fname, self.project_base_path, parent_context=False, child_context=False,
                                    header_max=0)
        output = fname_summary.summarize()
        expected_output = '\npr_agent/static_analysis/tests/example_files/calc.java:\n...⋮...\n 16│public class CalculatorUI {\n 17│\n...⋮...\n 84│    public double calculate(double firstNumber, double secondNumber, char operator) {\n...⋮...\n103│    private void initThemeSelector() {\n...⋮...\n118│    private void initInputScreen(int[] columns, int[] rows) {\n...⋮...\n127│    private void initCalculatorTypeSelector() {\n...⋮...\n151│    private void initButtons(int[] columns, int[] rows) {\n...⋮...\n510│    private JComboBox<String> createComboBox(String[] items, int x, int y, String toolTip) {\n...⋮...\n520│    private JButton createButton(String label, int x, int y) {\n...⋮...\n531│    private void applyTheme(Theme theme) {\n...⋮...\n'
        assert output == expected_output
