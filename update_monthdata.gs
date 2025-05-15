function duplicateRowsPreserveFormulas() {
  // 0. 先拿一把鎖，避免重複觸發時衝突
  var lock = LockService.getScriptLock();
  if (!lock.tryLock(10000)) {
    // 最多等 30 秒
    Logger.log("無法取得鎖，稍後再試");
    return;
  }

  try {
    // 1. 打開指定試算表
    var SPREADSHEET_ID = "1SzsPFCEtwV2om6r_2N0eBS66YsEKB72oOAvvThf7GRg";
    var ss = SpreadsheetApp.openById(SPREADSHEET_ID);
    var sheet = ss.getSheetByName("New MonthlyTable");
    if (!sheet) throw new Error("找不到工作表 'New MonthlyTable'");

    // 2. 從 G2 讀取目標年月（Date 物件）
    var cellValue = sheet.getRange("G2").getValue();
    if (!(cellValue instanceof Date)) {
      throw new Error("請在 G2 放入日期 (例：2025/05/01)");
    }
    var ty = cellValue.getFullYear(),
      tm = cellValue.getMonth();

    // 3. 取得第 2 列之後所有資料
    var lastRow = sheet.getLastRow();
    if (lastRow < 2) {
      Logger.log("沒有資料可以處理");
      return;
    }
    var lastCol = sheet.getLastColumn();
    var bodyVals = sheet.getRange(2, 1, lastRow - 1, lastCol).getValues();

    // 4. 篩選出 G 欄同年同月的列，並算出 +1 月的新日期
    var matches = [],
      newDates = [];
    bodyVals.forEach(function (row, i) {
      var d = row[6];
      if (d instanceof Date && d.getFullYear() === ty && d.getMonth() === tm) {
        matches.push(i);
        newDates.push(new Date(d.getFullYear(), d.getMonth() + 1, d.getDate()));
      }
    });

    var count = matches.length;
    if (count === 0) {
      Logger.log(
        "G2=" +
          Utilities.formatDate(
            cellValue,
            ss.getSpreadsheetTimeZone(),
            "yyyy-MM"
          ) +
          " 無符合列"
      );
      return;
    }

    // 5. 插入空白列 + copyTo 保留公式 + 覆寫 G 欄
    sheet.insertRowsBefore(2, count);
    matches.forEach(function (relIdx, j) {
      var srcRow = relIdx + 2 + count; // 原本第 (2+relIdx) 行，已被推下 count 行
      var dstRow = 2 + j; // 新插入的第 j 行
      sheet
        .getRange(srcRow, 1, 1, lastCol)
        .copyTo(sheet.getRange(dstRow, 1, 1, lastCol), { contentsOnly: false });
      sheet.getRange(dstRow, 7).setValue(newDates[j]);
    });

    Logger.log("成功插入 " + count + " 列");
  } catch (e) {
    // 如果想做重試，可以在這邊加上重試邏輯
    Logger.log("run failed: " + e);
    throw e;
  } finally {
    // 6. 釋放鎖
    lock.releaseLock();
  }
}
