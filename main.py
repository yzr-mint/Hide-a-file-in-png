import sys
from PyQt5.QtWidgets import QTextEdit, QApplication, QWidget, QPushButton, QVBoxLayout, QLineEdit, QFileDialog, QMessageBox
from PyQt5.QtCore import Qt
from io import StringIO

output=sys.stdout
code_byte=0
class FileDragDropWidget(QLineEdit):
	def __init__(self, describe = "拖动文件到这里或者点击选择文件", parent=None):
		super(FileDragDropWidget, self).__init__(parent)
		self.setDragEnabled(True)
		self.setPlaceholderText(describe)
	
	def dragEnterEvent(self, e):
		if e.mimeData().hasUrls():
			e.accept()
		else:
			e.ignore()

	def dropEvent(self, e):
		files = [url.toLocalFile() for url in e.mimeData().urls()]
		if files:
			self.setText(files[0])  # 只取第一个文件

class App(QWidget):
	def __init__(self):
		super().__init__()
		self.initUI()

	def initUI(self):
		self.setWindowTitle('隐藏文件')
		self.setGeometry(500, 500, 500, 300)

		self.layout = QVBoxLayout()

		self.filePaths = [FileDragDropWidget("输入png"), 
					FileDragDropWidget("隐藏文件（留空则为解隐藏）"), 
					FileDragDropWidget("输出文件")
					]
		for filePath in self.filePaths:
			self.layout.addWidget(filePath)

		self.codebox = FileDragDropWidget("密码：N个字节的二进制字符串，留空则不加密")
		self.layout.addWidget(self.codebox)

		self.outputTextBox = QTextEdit(self)
		self.outputTextBox.setReadOnly(True)  # 设置为只读模式
		self.outputTextBox.setFixedHeight(100)  # 可以根据需要调整高度
		self.layout.addWidget(self.outputTextBox)


		self.runButton = QPushButton('运行')
		self.runButton.clicked.connect(self.runFunction)
		self.layout.addWidget(self.runButton)

		self.setLayout(self.layout)

	def runFunction(self):
		global code_byte
		code = self.codebox.text()
		if code:
			code_byte = int(code, 2).to_bytes(len(code) // 8, byteorder='big')
		else:
			code_byte = 0
			
		args = [filePath.text() for filePath in self.filePaths if filePath.text()]

		output_stream = StringIO()
		global output
		output = output_stream
		# 假设FF是导入的或定义在某处的函数
		try:
			FF(*args)  # 使用解包操作符调用函数，适应不定数量的参数
			output_content = output_stream.getvalue()
			self.outputTextBox.append(output_content)
			QMessageBox.information(self, "成功", "执行完毕！")
		except Exception as e:
			QMessageBox.critical(self, "错误", f"执行出错: {str(e)}")
		output_stream.close()

def xor_encrypt_decrypt(input_bytes, code_byte):
    code_length = len(code_byte)
    # 对每个输入字节应用XOR操作，循环使用code字节
    return bytes([b ^ code_byte[i % code_length] for i, b in enumerate(input_bytes)])

def extract_data_from_png(secred_file_path, recovered_file_path):
	with open(secred_file_path, 'rb') as file:
		content = file.read()
	
	# PNG文件结束标志
	iend = b'IEND'
	iend_index = content.rfind(iend)
	
	# 检查是否找到IEND块
	if iend_index != -1:
		# IEND块后紧跟的4字节是CRC，跳过这8字节获取真正的结束位置
		start_of_hidden_data = iend_index + len(iend) + 4
		hidden_data = content[start_of_hidden_data:]
		
		if hidden_data:
			if code_byte:
				hidden_data = xor_encrypt_decrypt(hidden_data, code_byte)
			with open(recovered_file_path, 'wb') as hidden_file:
				hidden_file.write(hidden_data)
			print(f"Hidden data extracted to {recovered_file_path}.", file = output)
		else:
			print("No hidden data found.", file = output)
	else:
		print("PNG end marker not found. Is this a valid PNG file?", file = output)
		
def append_file_to_png(png_path, file_to_append_path, output_path):
	# 读取PNG文件内容
	with open(png_path, 'rb') as png_file:
		png_content = png_file.read()
	
	# 读取要附加的文件内容
	with open(file_to_append_path, 'rb') as file_to_append:
		file_content = file_to_append.read()
	if code_byte:
		file_content = xor_encrypt_decrypt(file_content, code_byte)
	combined_content = png_content + file_content
	with open(output_path, 'wb') as output_file:
		output_file.write(combined_content)

def FF(*files):
	if len(files) == 3:
		print("3 paths are found. Ready to hide something...", file = output)
		png_path = files[0]
		file_to_append_path = files[1]
		output_path = files[2]
		append_file_to_png(png_path, file_to_append_path, output_path)
		print(f"File {file_to_append_path} has been appended to {png_path} and saved to {output_path}", file = output)
	elif len(files) == 2:
		print("2 paths are found. Ready to recover something...", file = output)
		png_path = files[0]
		output_path = files[1]
		extract_data_from_png(png_path, output_path)
		print(f"File {output_path} has been recovered from {png_path}", file = output)
	else:
		print("For anyone want to hide something:", file = output)
		print("    python script.py <png_path> <file_to_append_path> <output_path>", file = output)
		print("Or you want to recover something:", file = output)
		print("    python script.py <png_path> <output_path>", file = output)

if __name__ == '__main__':
	app = QApplication(sys.argv)
	ex = App()
	ex.show()
	sys.exit(app.exec_())
