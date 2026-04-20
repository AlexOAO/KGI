# 專案三：七分鐘衝刺閱讀器與情境式銜接機制

## 業務背景（專案初衷）
成人學習者，尤其是忙碌的金融業務員，需要「情境脈絡」才能有效吸收資訊。如果業務員打開一個學習模組，映入眼簾的只是一堵文字牆，他們的認知負荷會瞬間飆升。透過明確顯示「來源文件」與「領域標籤」，我們能在內容開始前先替他們的大腦暖機。

此外，清楚預告「即將進行測驗」能激活學習者的**「主動閱讀模式」**。他們不再只是漫無目的地滑過內容，而是帶著目標在搜尋資訊——因為他們知道接下來要被考核。這種緊密的回饋循環，正是系統動態學應用於人類學習的核心原則。

## 使用者介面 (UI) 設計

### 1. 「衝刺前」啟動畫面
在計時器開始前，使用者會先看到一張資訊卡，從系統拉取相關知識的詮釋資料 (Metadata)，內容包含：
* **原始文件標題：**（例如：「2026 年 FSC 旅遊保險交叉銷售指引」）
* **領域標籤：**（例如：`#法規合規`、`#旅遊保險`）
* **行動呼籲 (CTA)：** 清楚的警示說明 —— 「你有 7 分鐘閱讀 5 張卡片，完成後立即進行 3 題測驗。」

### 2. 可滑動的閱讀介面
採用**行動優先 (Mobile-First)**、類 Instagram 限時動態風格的滑動介面。
* **頂部狀態列：** 顯示進度指示（如：第 2/5 張）、領域標籤。
* **倒數計時：** 顯眼的嚴格倒數計時器，營造微迫切感。

### 3. 「時間到 / 交接」畫面
當計時器歸零，或使用者滑完最後一張卡片時，畫面會立即鎖定並播放簡潔的 CSS 動畫，顯示：「**衝刺完成。正在生成你的測驗⋯⋯**」，隨後自動導向測驗介面。

---

## 使用者需求規格 (Technical Spec)

1.  **詮釋資料擷取：** 前端必須向後端查詢，不只取得閃卡內容，還要取得父模組的詮釋資料（領域與來源文件）。
2.  **嚴格的狀態管理：** * 計時器邏輯必須與瀏覽器的 **Visibility API** 綁定


# 數據庫設計方案 (Database Design Specification)

此資料庫設計旨在作為內容生成 (P1) 與學習遙測 (P2) 之間的橋樑，展示對資料庫正規化 (Normalization) 與外鍵關聯 (Foreign Keys) 的深度理解。

---

## 1. FlashcardPages (內容片段)
**用途：** 儲存微模組內的具體教學內容。

| 欄位名稱 (Field) | 類型 (Type) | 說明 (Description) |
| :--- | :--- | :--- |
| `page_id` | Primary Key | 唯一識別碼 |
| `module_id` | Foreign Key | 關聯至 P1 的 MicroModules |
| `sequence_number` | Integer | 排序序號 (例如：1, 2, 3) |
| `page_content_json` | JSON / Text | 頁面內容，包含文本與可選圖片路徑 |

---

## 2. SprintSessions (閱讀行為追蹤)
**用途：** 記錄使用者在閱讀階段的專注度與行為遙測數據。

| 欄位名稱 (Field) | 類型 (Type) | 說明 (Description) |
| :--- | :--- | :--- |
| `sprint_id` | Primary Key | 唯一識別碼 |
| `agent_id` | UUID / INT | 使用者或代理人識別碼 |
| `module_id` | Foreign Key | 關聯至該學習模組 |
| `start_timestamp` | DateTime | 階段開始時間 |
| `end_timestamp` | DateTime | 階段結束時間 |
| `tab_switch_count` | Integer | 分頁切換次數 (評估專注度指標) |
| `completion_status` | Enum | 完成狀態 ('finished_early', 'timed_out', 'abandoned') |

---

## 3. LearningJourney_Map (學習歷程對照表)
**用途：** 此表為「連接組織」，將閱讀階段 (Sprint) 與測試階段 (Quiz) 直接關聯，為 AI 分析提供訓練基礎。

| 欄位名稱 (Field) | 類型 (Type) | 說明 (Description) |
| :--- | :--- | :--- |
| `journey_id` | Primary Key | 唯一識別碼 |
| `sprint_id` | Foreign Key | 關聯至本次 P3 的閱讀 Session |
| `quiz_session_id` | Foreign Key | 關聯至 P2 的測驗 Session |

---