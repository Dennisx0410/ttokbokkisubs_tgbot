# ttokbokkisubs_bot (#v1.14)
A telegram bot for dividing videos into time segments and extracting subtitles from youtube.

## Installation

### 1. 下載整個repo
```bash
# change ${PAT} to your own personal access token of github
git clone https://${PAT}@github.com/Dennisx0410/ttokbokkisubs_bot.git 
```

### 2. 安裝python library requirements
```bash
python3 -m pip install --upgrade pip
cd ttokbokkisubs_bot
pip install -r requirements.txt
```

### 3. 下載cresidential.json, cert.pem, private.key放到repo directory
Ask LcYxT or Dennisx0410 for the files.
<br><br>
## Start bot

Start the bot using python3 and stop by pressing ctrl+c
```bash
python3 ttokbokkisubs_bot.py 
```
<br>

## ttokbokkisubs_bot 現有command

```/newjob``` - 新增工作報名表

```/reg``` - 報名

```/divpart``` - 跟據片長或以keyword/URL搜尋影片並分part，回傳分好part嘅txt(如果有)

```/banner``` - 產生aegisub banner

```/title``` - reply名單加標題

```/doc``` -reply名單加google doc

```/edit``` - edit reply嘅bot message

```/delete``` - delete reply嘅bot message

```/done``` - reply名單講做完邊part

```/undone``` - reply名單刪某part嘅tick

```/announce``` - 用bot send message到自己揀嘅group **(admin only)**

```/closejob``` - 從進度表移除已完成工作

```/info``` - bot資訊

```/updatenote``` - 更新內容

```/setting``` - set bot模式

```/help``` - 睇bot有咩command
