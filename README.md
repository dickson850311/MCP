# MCP

MCP (Model Context Protocol) integrations and reusable engineering-agent skills.

## Skills

- [intesim-native-post-contours](skills/intesim-native-post-contours/) — INTESIM 8.0 native Post contour export and DOCX figure replacement.
- [simdroid-ec-thermal-workflow](skills/simdroid-ec-thermal-workflow/) — 伏图电子散热（Simdroid Electronic Cooling V2026.7.x）从 STEP 导入到 Word 报告的 11 步热仿真全流程，含已验证脚本、参数基线、API cookbook 与输出校验。

## Quick start

```powershell
cd skills\simdroid-ec-thermal-workflow\scripts
powershell -ExecutionPolicy Bypass -File .\run_all_ec.ps1
```

首次使用先编辑 `skills/simdroid-ec-thermal-workflow/assets/project_config.json`，把 `install_root`、`project_root`、`step_file` 和 `files.*` 改成自己的路径。`01–08` 用伏图自带 Python，`09–11` 用系统 Python（需 `pymupdf`、`python-docx`），`run_ec.ps1` 会自动切换。
