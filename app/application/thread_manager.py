import threading
from logging import getLogger

logger = getLogger(__name__)


class ThreadTask:
    def __init__(self, name: str):
        self.name = name
        self.thread = None
        self.stop_event = threading.Event()

    def start(self) -> str:
        """タスクを開始する。"""
        try:
            if self.thread is None or not self.thread.is_alive():
                self.stop_event.clear()  # 前回の停止フラグをリセット
                self.thread = threading.Thread(target=self.run, name=self.name)
                self.thread.start()
                logger.info(f"{self.name} started.")
                return "開始しました"
            else:
                logger.info(f"{self.name} is already running.")
                return "実行中です"
        except Exception as e:
            logger.exception(f"Failed to start {self.name}: {e}")
            self.stop_event.set()
            return "開始できませんでした"

    def stop(self):
        """タスクを停止する。"""
        if self.thread is not None and self.thread.is_alive():
            self.stop_event.set()  # 停止を指示
            self.thread.join()
            logger.info(f"{self.name} stopped.")
            self.thread = None
            return "停止しました"
        else:
            logger.info(f"{self.name} is not running.")
            return "動作していません"

    def run(self):
        raise NotImplementedError("Subclasses must implement this method.")
