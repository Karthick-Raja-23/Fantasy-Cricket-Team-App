import sys
import sqlite3
from evaluate_ui import Ui_Dialog
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QInputDialog, QMessageBox
from fantasy_ui import Ui_MainWindow


class EvaluateDialog(QtWidgets.QDialog):
    def __init__(self):
        super().__init__()
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)

        self.load_data()

        self.ui.btnCalculate.clicked.connect(self.calculate_score)

        self.ui.tblScore.horizontalHeader().setStretchLastSection(True)
        self.ui.tblScore.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)

    def  load_data(self):
        conn = sqlite3.connect("fantasy.db")
        cur = conn.cursor()

        cur.execute("SELECT name FROM teams")
        teams = [row[0] for row in cur.fetchall()]
        self.ui.cmbTeam.addItems(teams)

        conn.close()

    def calculate_score(self):

        team_name = self.ui.cmbTeam.currentText()

        conn = sqlite3.connect("fantasy.db")
        cur = conn.cursor()

        cur.execute("SELECT players FROM teams WHERE name=?", (team_name,))
        players_str = cur.fetchone()[0]
        players = players_str.split(",")

        self.ui.tblScore.setRowCount(0)

        total_score = 0

        for player in players:
            cur.execute("""
                        SELECT runs, hundreds, fifties 
                        FROM stats WHERE player=? """, (player,))
            
            data = cur.fetchone()

            if not data:
                continue

            runs, hundreds, fifties = data

            score = 0

            score += runs//2
            score += hundreds * 10
            score += fifties * 5

            total_score += score

            row = self.ui.tblScore.rowCount()
            self.ui.tblScore.insertRow(row)
            self.ui.tblScore.setItem(row, 0, QtWidgets.QTableWidgetItem(player))
            self.ui.tblScore.setItem(row, 1, QtWidgets.QTableWidgetItem(str(score)))

        conn.close()

        QtWidgets.QMessageBox.information(
            self,
            "Final Score",
            f"Team: {team_name}\n\nTotal Points: {total_score}"
        )

class FantasyApp(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.disable_ui()

        self.ui.actionNew_Team.triggered.connect(self.new_team)

        self.ui.rbBAT.toggled.connect(lambda: self.load_players("BAT"))
        self.ui.rbBOW.toggled.connect(lambda: self.load_players("BWL"))
        self.ui.rbAR.toggled.connect(lambda: self.load_players("AR"))
        self.ui.rbWK.toggled.connect(lambda: self.load_players("WK"))

        self.total_points = 1000
        self.points_used = 0

        self.count_bat = 0
        self.count_bwl = 0
        self.count_ar = 0
        self.count_wk = 0

        self.ui.listAvailable.itemDoubleClicked.connect(self.add_player)

        self.ui.btnAdd.clicked.connect(self.add_selected_player)

        self.ui.listSelected.itemDoubleClicked.connect(self.remove_player)

        self.ui.actionSave_Team.triggered.connect(self.save_team)

        self.ui.actionEvaluate_Score.triggered.connect(self.evaluate_score)

    def add_selected_player(self):
        item = self.ui.listAvailable.currentItem()
        if item:
            self.add_player(item)
        
    def add_player(self, item):

        player_name = item.text()

        conn = sqlite3.connect("fantasy.db")
        cur = conn.cursor()

        cur.execute("SELECT value, ctg FROM stats WHERE player=?", (player_name,))
        result = cur.fetchone()

        conn.close()

        if not result:
            return
        
        value, category = result

        if self.ui.listSelected.count() >= 11:
            QMessageBox.warning(self, "Error", "You can select only 11 players!")
            return
        
        if category == "WK" and self.count_wk >= 1:
            QMessageBox.warning(self, "Error", "Only 1 Wicketkeeper allowed! ")
            return
        
        if self.points_used + value > self.total_points:
            QMessageBox.warning(self, "Error", "Not enough points! ")
            return
        
        if category == "BAT":
            self.count_bat += 1
        elif category == "BWL":
            self.count_bwl += 1
        elif category == "AR":
            self.count_ar += 1
        elif category == "WK":
            self.count_wk += 1

        if player_name in [self.ui.listSelected.item(i).text() for i in range(self.ui.listSelected.count())]:
            return

        self.ui.listSelected.addItem(player_name)
        self.ui.listAvailable.takeItem(self.ui.listAvailable.row(item))

        self.points_used += value
        self.ui.lblPointsUsed.setText(f"Points Used: {self.points_used}")
        self.ui.Pavl.setText(f"Points Available: {self.total_points - self.points_used}")

        self.ui.lblBAT.setText(f"Batsmen (BAT) {self.count_bat}")
        self.ui.lblBOW.setText(f"Bowlers (BOW) {self.count_bwl}")
        self.ui.lblAR.setText(f"Allrounders (AR) {self.count_ar}")
        self.ui.lblWK.setText(f"Wicket-keeper (WK) {self.count_wk}")

    def remove_player(self, item):

        player_name = item.text()

        conn = sqlite3.connect("fantasy.db")
        cur = conn.cursor()

        cur.execute("SELECT value, ctg FROM stats WHERE player=?", (player_name,))
        value, category = cur.fetchone()

        conn.close()

        if category == "BAT":
            self.count_bat -= 1
        elif category == "BWL":
            self.count_bwl -= 1
        elif category == "AR":
            self.count_ar -= 1
        elif category == "WK":
            self.count_wk -= 1

        self.ui.listAvailable.addItem(player_name)
        self.ui.listSelected.takeItem(self.ui.listSelected.row(item))

        self.points_used -= value

        self.ui.lblPointsUsed.setText(f"Points Used: {self.points_used}")
        self.ui.Pavl.setText(f"Points Available: {self.total_points - self.points_used}")

        self.ui.lblBAT.setText(f"Batsmen (BAT) {self.count_bat}")
        self.ui.lblBOW.setText(f"Bowlers (BOW) {self.count_bwl}")
        self.ui.lblAR.setText(f"Allrounders (AR) {self.count_ar}")
        self.ui.lblWK.setText(f"Wicket-keeper (WK) {self.count_wk}")

    def disable_ui(self):
        self.ui.rbBAT.setEnabled(False)
        self.ui.rbBOW.setEnabled(False)
        self.ui.rbAR.setEnabled(False)
        self.ui.rbWK.setEnabled(False)
        self.ui.listAvailable.setEnabled(False)
        self.ui.listSelected.setEnabled(False)
        self.ui.btnAdd.setEnabled(False)

    def enable_ui(self):
        self.ui.rbBAT.setEnabled(True)
        self.ui.rbBOW.setEnabled(True)
        self.ui.rbAR.setEnabled(True)
        self.ui.rbWK.setEnabled(True)
        self.ui.listAvailable.setEnabled(True)
        self.ui.listSelected.setEnabled(True)
        self.ui.btnAdd.setEnabled(True)

    def new_team(self):
        text, ok = QInputDialog.getText(self, "New Team", "Enter Team Name: ")

        if ok and text != "":
            self.ui.lblTeamName.setText(f"Team Name : {text}")
            self.enable_ui()

        else:
            QMessageBox.warning(self, "Error", "team name cannot be empty!")

    def save_team(self):

        if self.ui.listSelected.count() != 11:
            QMessageBox.warning(self, "error", "Select exactly 11 player!")
            return
        
        if self.count_bat < 4 or self.count_bwl < 3 or self.count_ar < 1 or self.count_wk !=1:
            QMessageBox.warning(self, "Error", "Team does not meet category requirements!")
            return
        
        team_name = self.ui.lblTeamName.text().replace("Team Name: ", "")

        players = []
        for i in range(self.ui.listSelected.count()):
            players.append(self.ui.listSelected.item(i).text())

        players_str = ",".join(players)

        conn = sqlite3.connect("fantasy.db")
        cur = conn.cursor()

        cur.execute("DELETE FROM teams WHERE name=?", (team_name,))

        cur.execute("INSERT INTO teams VALUES (?,?,?)", (team_name, players_str, self.points_used))

        conn.commit()
        conn.close()

        QMessageBox.information(self, "Success", "Team saved successfully!")

    def load_players(self, category):

        if not self.sender().isChecked():
            return
        
        self.ui.listAvailable.clear()

        conn = sqlite3.connect("fantasy.db")
        cur = conn.cursor()

        cur.execute("SELECT player FROM stats WHERE ctg=?", (category,))
        players = cur.fetchall()

        selected_players = []
        for i in range(self.ui.listSelected.count()):
            selected_players.append(self.ui.listSelected.item(i).text())

        for player in players:
            if player[0] not in selected_players:
                self.ui.listAvailable.addItem(player[0])

        conn.close()

    def evaluate_score(self):
        dialog = EvaluateDialog()
        dialog.exec_()

        
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = FantasyApp()
    window.show()
    sys.exit(app.exec_())