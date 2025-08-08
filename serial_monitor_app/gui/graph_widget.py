import sys
from PySide6.QtWidgets import QVBoxLayout, QWidget
from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas

class MplGraphWidget(QWidget):
    """
    Matplotlibグラフを表示し、ホバーで座標を表示する機能を持つウィジェット。
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.figure = Figure(figsize=(5, 4), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        self.axes = self.figure.add_subplot(111)

        layout = QVBoxLayout()
        layout.addWidget(self.canvas)
        self.setLayout(layout)

        self.y_limits = None  # (min, max) or None for autoscale
        self.lines = []  # For multi-channel plots

        # グラフを初期化
        self.init_plot()

        # ホバー時に表示する注釈 (Annotation) を作成
        self.annot = self.axes.annotate("", xy=(0, 0), xytext=(20, 20),
                                        textcoords="offset points",
                                        bbox=dict(boxstyle="round", fc="w", ec="k", lw=1),
                                        arrowprops=dict(arrowstyle="->"))
        self.annot.set_visible(False)

        # マウス移動イベントを接続
        self.canvas.mpl_connect("motion_notify_event", self.hover)

    def plot_sample_data(self):
        """サンプルデータをプロットします。実際のデータプロット処理に置き換えてください。"""
        x = np.linspace(0, 10, 50)
        y = np.sin(x) * np.exp(-x/5)
        self.line, = self.axes.plot(x, y, 'o-') # 'o-'で点と線をプロット
        self.axes.set_title("Sample Data Plot")
        self.axes.set_xlabel("Time (s) or Address")
        self.axes.set_ylabel("Value")
        self.canvas.draw()

    def update_plot(self, x_data, y_data):
        """グラフのデータを新しいデータで更新します。"""
        self.line.set_data(x_data, y_data)
        self.axes.relim() # 軸の範囲を再計算
        self.axes.autoscale_view(True, True, True) # 軸のスケールを自動調整
        self.canvas.draw_idle()

    def update_annot(self, ind):
        """注釈の位置とテキストを更新します。"""
        pos = self.line.get_xydata()[ind["ind"][0]]
        self.annot.xy = pos
        text = f"X: {pos[0]:.2f}\nY: {pos[1]:.2f}"
        self.annot.set_text(text)
        self.annot.get_bbox_patch().set_alpha(0.7)

    def hover(self, event):
        """マウスホバーイベントのハンドラ。"""
        vis = self.annot.get_visible()
        if event.inaxes == self.axes:
            # line.contains は、マウスイベントがデータ点の近くにあるかをチェックします
            cont, ind = self.line.contains(event)
            if cont:
                self.update_annot(ind)
                self.annot.set_visible(True)
                self.canvas.draw_idle() # 効率的な再描画
            else:
                if vis:
                    self.annot.set_visible(False)
                    self.canvas.draw_idle()