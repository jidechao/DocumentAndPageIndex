<div align="center">
  
<a href="https://vectify.ai/pageindex" target="_blank">
  <img src="https://github.com/user-attachments/assets/46201e72-675b-43bc-bfbd-081cc6b65a1d" alt="PageIndex Banner" />
</a>

<br/>
<br/>

<p align="center">
  <a href="https://trendshift.io/repositories/14736" target="_blank"><img src="https://trendshift.io/api/badge/repositories/14736" alt="VectifyAI%2FPageIndex | Trendshift" style="width: 250px; height: 55px;" width="250" height="55"/></a>
</p>

<p align="center"><i>基于推理的RAG&nbsp; ✧ &nbsp;无需向量数据库&nbsp; ✧ &nbsp;无需文本分块&nbsp; ✧ &nbsp;类人检索</i></p>

<h4 align="center">
  <a href="https://vectify.ai">🏠 主页</a>&nbsp; • &nbsp;
  <a href="https://dash.pageindex.ai">🖥️ 仪表板</a>&nbsp; • &nbsp;
  <a href="https://pageindex.ai/mcp">🔌 MCP</a>&nbsp; • &nbsp;
  <a href="https://docs.pageindex.ai/quickstart">📚 文档</a>&nbsp; • &nbsp;
  <a href="https://discord.com/invite/VuXuf29EUj">💬 Discord</a>&nbsp; • &nbsp;
  <a href="https://ii2abc2jejf.typeform.com/to/tK3AXl8T">✉️ 联系我们</a>&nbsp;
</h4>
  
</div>

---

#### 🚨 **新版本发布:** [PageIndex MCP](https://github.com/VectifyAI/pageindex-mcp)

将 PageIndex 引入 Claude、Cursor 及任何支持 MCP 的智能体。以类人的、基于推理的方式与长篇 PDF 对话 📖

#  📄 PageIndex 简介

您是否对长篇幅专业文档的向量数据库检索准确率感到沮丧？传统的基于向量的 RAG 依赖语义*相似性*而非真正的*相关性*。但**相似性 ≠ 相关性** —— 我们在检索中真正需要的是**相关性**，而这需要**推理**。在处理需要领域专业知识和多步推理的专业文档时，相似性搜索往往表现不佳。

受 AlphaGo 启发，我们提出了 **[PageIndex](https://vectify.ai/pageindex)**，一个**基于推理的 RAG** 系统，它通过**树搜索**模拟**人类专家**如何浏览和从长文档中提取知识，使 LLM 能够通过*思考*和*推理*找到最相关的文档部分。它通过两个步骤执行检索：

1. 为文档生成一个"目录"**树结构索引**
2. 通过**树搜索**执行基于推理的检索

<div align="center">
    <img src="https://docs.pageindex.ai/images/cookbook/vectorless-rag.png" width="90%">
</div>

### 💡 特性

与传统基于向量的 RAG 相比，PageIndex 具有以下特点：
- **无需向量**：利用文档结构和 LLM 推理进行检索。
- **无需分块**：文档按自然章节组织，而非人工分块。
- **类人检索**：模拟人类专家如何浏览和从复杂文档中提取知识。
- **透明的检索过程**：基于推理的检索 —— 告别近似的向量搜索（"氛围检索"）。

PageIndex 驱动的基于推理的 RAG 系统在 FinanceBench 上达到了 [98.7% 的准确率](https://github.com/VectifyAI/Mafin2.5-FinanceBench)，在专业文档分析中展现了最先进的性能（详见我们的[博客文章](https://vectify.ai/blog/Mafin2.5)）。

### 🚀 部署选项
- 🛠️ 自托管 — 使用此开源仓库在本地运行
- ☁️ **[云服务](https://dash.pageindex.ai/)** — 通过我们的 🖥️ [仪表板](https://dash.pageindex.ai/) 或 🔌 [API](https://docs.pageindex.ai/quickstart) 即时试用，无需设置

### ⚡ 快速上手

查看这个简单的 [*无向量 RAG 笔记本*](https://github.com/VectifyAI/PageIndex/blob/main/cookbook/pageindex_RAG_simple.ipynb) — 一个使用 **PageIndex** 的最小化、可动手实践的、基于推理的 RAG 流水线。
<p align="center">
<a href="https://colab.research.google.com/github/VectifyAI/PageIndex/blob/main/cookbook/pageindex_RAG_simple.ipynb">
    <img src="https://img.shields.io/badge/在_Colab中打开-使用_PageIndex的无向量_RAG-orange?style=for-the-badge&logo=googlecolab" alt="在 Colab 中打开"/>
  </a>
</p>

---

# 📦 PageIndex 树结构
PageIndex 可以将冗长的 PDF 文档转换为语义**树结构**，类似于_"目录"_，但针对大型语言模型的使用进行了优化。它非常适用于：财务报告、监管文件、学术教科书、法律或技术手册，以及任何超出 LLM 上下文限制的文档。

以下是一个输出示例。查看更多 [示例文档](https://github.com/VectifyAI/PageIndex/tree/main/tests/pdfs) 和 [生成的树结构](https://github.com/VectifyAI/PageIndex/tree/main/tests/results)。

```
...
{
  "title": "金融稳定",
  "node_id": "0006",
  "start_index": 21,
  "end_index": 22,
  "summary": "美联储...",
  "nodes": [
    {
      "title": "监测金融脆弱性",
      "node_id": "0007",
      "start_index": 22,
      "end_index": 28,
      "summary": "美联储的监测..."
    },
    {
      "title": "国内与国际合作与协调",
      "node_id": "0008",
      "start_index": 28,
      "end_index": 31,
      "summary": "2023年，美联储协作..."
    }
  ]
}
...
```

您可以使用此开源仓库生成 PageIndex 树结构，或者试用我们的 ☁️ **[云服务](https://dash.pageindex.ai/)** — 通过我们的 🖥️ [仪表板](https://dash.pageindex.ai/) 或 🔌 [API](https://docs.pageindex.ai/quickstart) 即时访问，无需设置。

---

# 🚀 包使用

您可以按照以下步骤从 PDF 文档生成 PageIndex 树。

### 1. 安装依赖

```bash
pip3 install --upgrade -r requirements.txt
```

### 2. 设置您的 OpenAI API 密钥

在根目录创建一个 `.env` 文件并添加您的 API 密钥：

```bash
CHATGPT_API_KEY=您的_openai_密钥_在此
```

### 3. 在您的 PDF 上运行 PageIndex

```bash
python3 run_pageindex.py --pdf_path /path/to/your/document.pdf
```

<details>
<summary><strong>可选参数</strong></summary>
<br>
您可以使用额外的可选参数来自定义处理过程：

```
--model                 使用的 OpenAI 模型 (默认: gpt-4o-2024-11-20)
--toc-check-pages       检查目录的页数 (默认: 20)
--max-pages-per-node    每个节点的最大页数 (默认: 10)
--max-tokens-per-node   每个节点的最大令牌数 (默认: 20000)
--if-add-node-id        添加节点 ID (是/否, 默认: 是)
--if-add-node-summary   添加节点摘要 (是/否, 默认: 是)
--if-add-doc-description 添加文档描述 (是/否, 默认: 是)
```
</details>

<details>
<summary><strong>Markdown 支持</strong></summary>
<br>
我们还为 PageIndex 提供了 Markdown 支持。您可以使用 `-md` 标志为 Markdown 文件生成树结构。

```bash
python3 run_pageindex.py --md_path /path/to/your/document.md
```

> 注意：在此功能中，我们使用 "#" 来确定节点标题及其级别。例如，"##" 是 2 级，"###" 是 3 级，依此类推。请确保您的 Markdown 文件格式正确。如果您的 Markdown 文件是从 PDF 或 HTML 转换而来，我们不建议使用此功能，因为大多数现有的转换工具无法保留原始层次结构。相反，请使用我们的 [PageIndex OCR](https://pageindex.ai/blog/ocr)（专为保留原始层次结构而设计）将 PDF 转换为 Markdown 文件，然后再使用此功能。
</details>

---

# ☁️ 使用 PageIndex OCR 改进树生成

此仓库旨在为简单的 PDF 生成 PageIndex 树结构，但许多实际用例涉及复杂的 PDF，这些 PDF 很难通过经典的 Python 工具解析。然而，从 PDF 文档中提取高质量文本仍然是一个不小的挑战。大多数 OCR 工具仅提取页面级内容，丢失了更广泛的文档上下文和层次结构。

为了解决这个问题，我们推出了 PageIndex OCR —— 第一个旨在保留文档全局结构的长上下文 OCR 模型。在识别跨文档页面的真实层次结构和语义关系方面，PageIndex OCR 显著优于其他领先的 OCR 工具，例如 Mistral 和 Contextual AI 的工具。

- 在我们的[仪表板](https://dash.pageindex.ai/)上体验 PageIndex OCR 的下一代 OCR 质量。
- 通过我们的 [API](https://docs.pageindex.ai/quickstart) 将 PageIndex OCR 无缝集成到您的技术栈中。

<p align="center">
  <img src="https://github.com/user-attachments/assets/eb35d8ae-865c-4e60-a33b-ebbd00c41732" width="90%">
</p>

---

# 📈 案例研究：FinanceBench 上的 Mafin 2.5

[Mafin 2.5](https://vectify.ai/mafin) 是一个最先进的、基于推理的 RAG 模型，专为金融文档分析设计。由 **PageIndex** 驱动，它在 [FinanceBench](https://arxiv.org/abs/2311.11944) 基准测试中达到了市场领先的 [**98.7% 准确率**](https://vectify.ai/blog/Mafin2.5) —— 显著优于传统的基于向量的 RAG 系统。

PageIndex 的分层索引使得能够从复杂的财务报告（如 SEC 文件和收益披露）中精确导航和提取相关内容。

👉 查看完整的 [基准测试结果](https://github.com/VectifyAI/Mafin2.5-FinanceBench) 和我们的 [博客文章](https://vectify.ai/blog/Mafin2.5) 以获取详细的比较和性能指标。

<div align="center">
  <a href="https://github.com/VectifyAI/Mafin2.5-FinanceBench">
    <img src="https://github.com/user-attachments/assets/571aa074-d803-43c7-80c4-a04254b782a3" width="90%">
  </a>
</div>

---

# 🔎 了解更多关于 PageIndex

### 资源与指南

- 📖 探索我们的 [教程](https://docs.pageindex.ai/doc-search) 获取实用指南和策略，包括*文档搜索*和*树搜索*。
- 🧪 浏览 [Cookbook](https://docs.pageindex.ai/cookbook/vectorless-rag-pageindex) 获取实用方法和高级用例。
- ⚙️ 参考 [API 文档](https://docs.pageindex.ai/quickstart) 了解集成细节和配置选项。

### ⭐ 支持我们

如果您喜欢我们的项目，请给我们一个星标。谢谢！

<p>
  <img src="https://github.com/user-attachments/assets/eae4ff38-48ae-4a7c-b19f-eab81201d794" width="60%">
</p>

### 联系我们

[![Twitter](https://img.shields.io/badge/Twitter-000000?style=for-the-badge&logo=x&logoColor=white)](https://x.com/VectifyAI)&nbsp;
[![LinkedIn](https://img.shields.io/badge/LinkedIn-0077B5?style=for-the-badge&logo=linkedin&logoColor=white)](https://www.linkedin.com/company/vectify-ai/)&nbsp;
[![Discord](https://img.shields.io/badge/Discord-5865F2?style=for-the-badge&logo=discord&logoColor=white)](https://discord.com/invite/VuXuf29EUj)&nbsp;
[![联系我们](https://img.shields.io/badge/联系我们-3B82F6?style=for-the-badge&logo=envelope&logoColor=white)](https://ii2abc2jejf.typeform.com/to/tK3AXl8T)

---

© 2025 [Vectify AI](https://vectify.ai)