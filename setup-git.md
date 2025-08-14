# Git 設定說明

## 初始化 Git 倉庫

請按照以下步驟將專案上傳到 GitHub：

### 1. 初始化本地 Git 倉庫
```bash
git init
```

### 2. 添加檔案到暫存區
```bash
git add .
```

### 3. 提交初始版本
```bash
git commit -m "Initial commit: 女神400速解小工具 v1.2.1"
```

### 4. 在 GitHub 上創建新倉庫
1. 前往 [GitHub](https://github.com)
2. 點擊 "New repository"
3. 倉庫名稱建議：`Artale400` 或 `goddess-400-tool`
4. 選擇 "Public" 或 "Private"
5. **不要**勾選 "Initialize this repository with a README"
6. 點擊 "Create repository"

### 5. 連接本地倉庫到 GitHub
```bash
git remote add origin https://github.com/你的用戶名/Artale400.git
git branch -M main
git push -u origin main
```

### 6. 創建 Release（可選）
```bash
git tag v1.2.1
git push origin v1.2.1
```

## 後續更新流程

### 日常開發
```bash
# 修改程式碼後
git add .
git commit -m "描述你的修改"
git push origin main
```

### 發布新版本
```bash
# 1. 更新版本號
# 2. 提交變更
git add .
git commit -m "Release v1.2.2"
git push origin main

# 3. 創建標籤
git tag v1.2.2
git push origin v1.2.2
```

## 注意事項

1. **不要上傳執行檔**：`.gitignore` 已經設定排除 `*.exe` 檔案
2. **不要上傳建置檔案**：`build/` 和 `dist/` 目錄會被自動排除
3. **保護敏感資訊**：確保沒有包含個人資訊或敏感資料
4. **更新 README**：記得更新 README.md 中的 GitHub 連結

## 建議的倉庫設定

### 在 GitHub 倉庫設定中：
1. **Description**: "一個基於 PyQt5 開發的桌面應用程式，提供快速查表功能"
2. **Topics**: `python`, `pyqt5`, `desktop-app`, `windows`, `gui`
3. **Website**: 可以留空或填寫個人網站
4. **Issues**: 啟用 Issues 功能
5. **Wiki**: 可選啟用
6. **Discussions**: 可選啟用

### 分支保護規則（可選）
- 保護 `main` 分支
- 要求 Pull Request 審查
- 要求狀態檢查通過
