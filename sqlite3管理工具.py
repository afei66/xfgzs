import sqlite3
import tkinter as tk
from tkinter import ttk, simpledialog, messagebox

print('-------欢迎使用sqlite3 轻量化管理工具----------------')
print('-------本工具由wxll-afei66创作  交流群：816663504 --------')
print('-------感谢选择使用 请勿将此软件用在非法用户谢谢配合 --------')
# 从数据库获取所有表的名称
def fetch_tables():
    with sqlite3.connect('sql.db') as conn:
        table_names = [table[0] for table in conn.execute("SELECT name FROM sqlite_master WHERE type='table';")]
    return ["请选择数据表"] + table_names

# 从指定的表获取数据
def fetch_data(table_name):
    with sqlite3.connect('sql.db') as conn:
        return conn.execute(f"SELECT * FROM {table_name}").fetchall()

# 获取指定表的结构
def fetch_structure(table_name):
    with sqlite3.connect('sql.db') as conn:
        return [column[1] for column in conn.execute(f"PRAGMA table_info({table_name})")]
    
def on_tree_select(event):
    for item in tree.selection():
        if 'notclickable' in tree.item(item, 'tags'):
            tree.selection_remove(item)
# 显示数据
def display_data(event):
    selected_table = table_dropdown.get()
    if selected_table == "请选择数据表":
        tree["columns"] = ["提示"]
        for col in tree["columns"]:
            tree.heading(col, text=col)
            tree.column(col, width=550)  # 或其它你想要的宽度

        for row in tree.get_children():
            tree.delete(row)

        tree.insert("", "end", values=["请选择一个数据库表"],tags=('notclickable',))
        return

    columns_structure = fetch_structure(selected_table)
    tree["columns"] = columns_structure + ["操作"]
    for col in columns_structure:
        tree.heading(col, text=col)
        tree.column(col, width=150)
    tree.heading("操作", text="操作")
    tree.column("操作", width=100)  # 设置操作列的宽度

    for row in tree.get_children():
        tree.delete(row)

    for record in fetch_data(selected_table):
     tree.insert("", "end", values=record + ("删除",), tags=('selectable',))
    tree.tag_bind('selectable', '<Double-1>', on_item_double_click)

# 双击进入编辑模式
def on_item_double_click(event):
    global edit_box  # 声明 edit_box 为全局变量
    item = tree.selection()[0]
    col = tree.identify_column(event.x).split('#')[-1]
    col = int(col)
    value = tree.item(item, 'values')

    # 检查选择的行是否为提示文本
    if "请选择一个数据库表" in value:
        return
    
    # 检查是否双击了“删除”标签
    if value[col - 1] == "删除":
        confirm = messagebox.askyesno("确认", "您确定要删除这行数据吗?")
        if confirm:
            delete_row(item, value[0])  # 假设第一个字段是唯一标识符，如ID
    else:
        x, y, width, height = tree.bbox(item, column=tree["columns"][col-1])
        edit_box = ttk.Entry(tree, justify='center')
        edit_box.place(x=x, y=y, width=width, height=height)
        edit_box.insert(0, value[col - 1])
        edit_box.focus_set()
        edit_box.bind('<Return>', lambda e: close_edit_box(item, col))
        edit_box.bind('<FocusOut>', lambda e: close_edit_box(item, col))

# 编辑完成，更新数据
def close_edit_box(item, col):
    global edit_box
    if edit_box: 
        tree.set(item, tree["columns"][col-1], edit_box.get())
        edit_box.destroy()
        update_database(item, col-1, tree.item(item, 'values')[col-1])

# 更新到数据库
def update_database(item, col, value):
    selected_table = table_dropdown.get()
    col_name = tree["columns"][col]
    primary_key = tree.item(item, 'values')[0] 
    col_names = fetch_structure(selected_table)
    with sqlite3.connect('sql.db') as conn:
        conn.execute(f"UPDATE {selected_table} SET {col_name} = ? WHERE {col_names[0]} = ?", (value, primary_key))
        conn.commit()

#响应更新事件
def update_display(table_name=None):
    if not table_name:
        table_name = table_dropdown.get()

    if not table_name:
        return

    columns = fetch_structure(table_name)
    columns.append("操作")
    tree["columns"] = columns
    for col in tree["columns"]:
        tree.heading(col, text=col)
        tree.column(col, width=150)

    for row in tree.get_children():
        tree.delete(row)

    for record in fetch_data(table_name):
        tree.insert("", "end", values=record + ("删除",), tags=('selectable',))

    tree.tag_bind('selectable', '<Double-1>', on_item_double_click)

# 提交新表单数据并创建数据表   
def create_new_table():
    def submit():
        table_name = table_name_entry.get()
        
        # 获取所有的字段名和字段类型
        columns = []
        for col_name, col_type in zip(col_name_entries, col_type_dropdowns):
            if col_name.get() and col_type.get():
                columns.append(f"{col_name.get()} {col_type.get()}")

        if not columns:
            messagebox.showwarning("提示", "请至少添加一个字段!")
            return

        try:
            with sqlite3.connect('sql.db') as conn:
                conn.execute(f"CREATE TABLE {table_name} ({', '.join(columns)})")
                conn.commit()

            # 更新下拉菜单的数据表列表
            table_names = fetch_tables()
            table_dropdown['values'] = table_names
            table_dropdown.set(table_name)
            
            # 提示用户数据表已成功创建
            messagebox.showinfo("提示", f"数据表 {table_name} 已成功创建!")
            update_display(table_name)

        except sqlite3.OperationalError as e:
            messagebox.showerror("错误", f"创建数据表时出错: {str(e)}")

        create_table_window.destroy()
        table_dropdown['values'] = fetch_tables()

    def add_column_entry():
        # 创建子框架来容纳字段名、字段类型和删除按钮
        frame = ttk.Frame(columns_frame)
        frame.pack(fill=tk.X, padx=10, pady=5)

        col_name_label = ttk.Label(frame, text="字段名称:")
        col_name_label.pack(side="left", padx=5)

        col_name = ttk.Entry(frame, width=15)
        col_name.pack(side="left", padx=5)

        col_type_label = ttk.Label(frame, text="字段类型:")
        col_type_label.pack(side="left", padx=5)
        
        datatype_options = ["INTEGER", "TEXT", "REAL", "BLOB", "VARCHAR(255)","如没有请手动输入"]
        col_type_dropdown = ttk.Combobox(frame, values=datatype_options, width=15)
        col_type_dropdown.set("TEXT")
        col_type_dropdown.pack(side="left", padx=5)

        delete_btn = ttk.Button(frame, text="删除", command=lambda: remove_column_entry(frame, col_name, col_type_dropdown))
        delete_btn.pack(side="left", padx=5)

        col_name_entries.append(col_name)
        col_type_dropdowns.append(col_type_dropdown)

    def remove_column_entry(frame, col_name, col_type_dropdown):
        col_name_entries.remove(col_name)
        col_type_dropdowns.remove(col_type_dropdown)
        frame.destroy()

    col_name_entries = []
    col_type_dropdowns = []
    

    create_table_window = tk.Toplevel(window)
    create_table_window.geometry('550x500')  # 子窗口大小（新增数据库框）
    create_table_window.title("创建新数据表")
    
    table_name_label = ttk.Label(create_table_window, text="数据表名称:")
    table_name_label.pack(pady=10)

    table_name_entry = ttk.Entry(create_table_window, width=30)
    table_name_entry.pack(pady=10, padx=10, fill=tk.X)

    # 设置滚动条和Canvas
    scroll_frame = ttk.Frame(create_table_window)
    scroll_frame.pack(pady=20, padx=10, fill=tk.BOTH, expand=True)
    canvas = tk.Canvas(scroll_frame, bd=0, highlightthickness=0)  # 去除边框
    scrollbar = ttk.Scrollbar(scroll_frame, orient="vertical", command=canvas.yview)
    columns_frame = ttk.Frame(canvas)
    canvas.pack(side="left", fill=tk.BOTH, expand=True)
    scrollbar.pack(side="right", fill="y")
    canvas.create_window((0, 0), window=columns_frame, anchor='nw')
    canvas.configure(yscrollcommand=scrollbar.set, scrollregion=canvas.bbox("all"))
    columns_frame.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    
    # 使Canvas支持鼠标滚轮滚动
    canvas.bind('<MouseWheel>', lambda e: canvas.yview_scroll(-1*(e.delta//120), 'units'))
    
    col_name_entries = []
    col_type_dropdowns = []

    add_column_btn = ttk.Button(columns_frame, text="添加新字段", command=add_column_entry)
    add_column_btn.pack(pady=10)

    action_frame = ttk.Frame(create_table_window)
    action_frame.pack(pady=20)

    submit_btn = ttk.Button(action_frame, text="创建数据表", command=submit)
    submit_btn.pack(side="left", padx=10)

    cancel_btn = ttk.Button(action_frame, text="关闭", command=create_table_window.destroy)
    cancel_btn.pack(side="right", padx=10)

    create_table_window.mainloop()

# 删除数据表函数
def delete_table():
    selected_table = table_dropdown.get()
    if not selected_table:
        messagebox.showwarning("提示", "请选择要删除的数据表")
        return

    confirm = messagebox.askyesno("确认", f"您确定要删除数据表 {selected_table} 吗？这个操作不可恢复!")
    if confirm:
        try:
            with sqlite3.connect('sql.db') as conn:
                conn.execute(f"DROP TABLE {selected_table}")
                conn.commit()
                
            table_names = fetch_tables()
            table_dropdown['values'] = table_names
            table_dropdown.set('')  # 清空当前选择
            
            # 清除treeview内容并重设列与提示
            tree["columns"] = ["提示"]
            for col in tree["columns"]:
                tree.heading(col, text=col)
                tree.column(col, width=550)  # 调整宽度以居中
            for row in tree.get_children():
                tree.delete(row)
            tree.insert("", "end", values=["请选择一个数据库表"],tags=('notclickable',))
            messagebox.showinfo("提示", f"数据表 {selected_table} 已成功删除!")
        except sqlite3.OperationalError as e:
            messagebox.showerror("错误", f"删除数据表时出错: {str(e)}")
    table_dropdown['values'] = fetch_tables()
            
# 编辑数据结构
def edit_structure():
    selected_table = table_dropdown.get()
    if not selected_table:
        messagebox.showwarning("提示", "请先选择一个数据表")
        return
    alter_table_structure()
    
def on_table_selected(event):
    selected_table = table_dropdown.get()

    # 如果选择的是 "请选择数据表"
    if selected_table == "请选择数据表":
        tree["columns"] = ["提示"]
        for col in tree["columns"]:
            tree.heading(col, text=col)
            tree.column(col, width=550)  # 或其它你想要的宽度

        for row in tree.get_children():
            tree.delete(row)

        tree.insert("", "end", values=["请选择一个数据库表"], tags=('notclickable',))

        # 隐藏相关按钮
        edit_structure_btn.grid_remove()
        rename_table_btn.grid_remove()
        edit_row_btn.grid_remove()
        return

    # 如果选择的是一个实际的数据表
    display_data(event)
    edit_structure_btn.grid(row=0, column=3, pady=10, padx=10)
    rename_table_btn.grid(row=0, column=4, pady=10, padx=10)
    edit_row_btn.grid(row=0, column=5, pady=10, padx=10)
window = tk.Tk()
window.title("SQLite3 数据管理器")

def add_column(parent_window):
    def submit_new_column():
        column_name = col_name_entry.get()
        column_type = col_type_dropdown.get()
        
        if not column_name or not column_type:
            messagebox.showwarning("警告", "字段名和字段类型不能为空!")
            return

        # 将新字段添加到临时字典
        pending_changes[column_name] = column_type
        parent_window.destroy()

    new_col_window = tk.Toplevel(parent_window)
    new_col_window.title("添加新字段")

    ttk.Label(new_col_window, text="字段名:").pack(pady=5, padx=10)
    col_name_entry = ttk.Entry(new_col_window)
    col_name_entry.pack(pady=5, padx=10, fill=tk.X)

    ttk.Label(new_col_window, text="字段类型:").pack(pady=5, padx=10)
    datatype_options = ["INTEGER", "TEXT", "REAL", "BLOB", "VARCHAR(255)"]
    col_type_dropdown = ttk.Combobox(new_col_window, values=datatype_options, width=15)
    col_type_dropdown.set("TEXT")
    col_type_dropdown.pack(pady=5, padx=10, fill=tk.X)

    ttk.Button(new_col_window, text="添加", command=submit_new_column).pack(pady=10)

  # 添加新数据结构
def save_changes(edit_window, table_name):
    with sqlite3.connect('sql.db') as conn:
        for column, column_type in pending_changes.items():
          
            try:
                conn.execute(f"ALTER TABLE {table_name} ADD COLUMN {column} {column_type}")
            except sqlite3.OperationalError as e:
                messagebox.showerror("错误", f"添加新列时出错: {str(e)}")
                return
    conn.commit()
    edit_window.destroy()
    messagebox.showinfo("提示", "更改已成功保存!")
    update_display(table_name)
pending_changes = {}   

# 修改数据结构UI
def alter_table_structure():
    def execute_structure_change():
        new_column_names = [e.get() for e in entries]
        altered = False

        # 确认删除
        for col, action in zip(columns, [d.get() for d in dropdowns]):
            if action == '删除':
                delete_column(selected_table, col)
                altered = True
            elif col != new_column_names[columns.index(col)]:
                rename_column(selected_table, col, new_column_names[columns.index(col)])
                altered = True

        if altered:
            messagebox.showinfo("提示", "成功修改数据结构!")
        else:
            messagebox.showinfo("提示", "没有做任何改变!")
        edit_structure_window.destroy()
        update_display()

    selected_table = table_dropdown.get()
    columns = fetch_structure(selected_table)

    edit_structure_window = tk.Toplevel(window)
    edit_structure_window.geometry('600x500')
    edit_structure_window.title(f"修改 {selected_table} 的结构")

    # 显示现有的列名，并提供更改名字的输入框
    entries = []
    dropdowns = []

    for col in columns:
        frame = ttk.Frame(edit_structure_window)
        frame.pack(fill=tk.X, padx=10, pady=5)

        label = ttk.Label(frame, text=f"字段:")
        label.pack(side=tk.LEFT, padx=5)

        entry = ttk.Entry(frame)
        entry.insert(0, col)
        entry.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
        entries.append(entry)
        options = ['保留', '删除']
        dropdown = ttk.Combobox(frame, values=options)
        dropdown.set('保留')
        dropdown.pack(side=tk.LEFT, padx=5)
        dropdowns.append(dropdown)
        # 新建一个框架来包含三个按钮
    btn_frame = ttk.Frame(edit_structure_window)
    btn_frame.pack(pady=20)

    # 将按钮添加到新框架中，并使用 grid 进行排列
    add_column_btn = ttk.Button(btn_frame, text="新增字段", command=lambda: add_new_column_ui(selected_table))
    add_column_btn.grid(row=0, column=0, padx=10)
    
    save_btn = ttk.Button(btn_frame, text="保存更改", command=execute_structure_change)
    save_btn.grid(row=0, column=1, padx=10)
    
    cancel_btn = ttk.Button(btn_frame, text="关闭", command=edit_structure_window.destroy)
    cancel_btn.grid(row=0, column=2, padx=10)

#重命名数据表中的字段
def rename_column(table_name, old_column_name, new_column_name):
    with sqlite3.connect('sql.db') as conn:
        # 获取当前表的所有列名
        columns = [column[1] for column in conn.execute(f"PRAGMA table_info({table_name})")]

        # 检查旧列名是否存在于列列表中
        if old_column_name not in columns:
            # 如果旧列名不存在，抛出错误
            raise ValueError(f"Column {old_column_name} not found in table {table_name}.")

        # 在列表中将旧列名替换为新列名
        new_columns = columns.copy()
        new_columns[new_columns.index(old_column_name)] = new_column_name

        # 创建一个新表，并将数据从旧表复制到新表
        new_table_name = table_name + "_new"
        conn.execute(f"CREATE TABLE {new_table_name} ({', '.join(new_columns)})")
        conn.execute(f"INSERT INTO {new_table_name} SELECT {', '.join(columns)} FROM {table_name}")
        
        # 删除旧表，并将新表重命名为旧表的名称
        conn.execute(f"DROP TABLE {table_name}")
        conn.execute(f"ALTER TABLE {new_table_name} RENAME TO {table_name}")
        
        # 提交更改
        conn.commit()

#修改数据表名
def rename_table(old_name, new_name):
    with sqlite3.connect('sql.db') as conn:
        try:
            conn.execute(f"ALTER TABLE {old_name} RENAME TO {new_name}")
            conn.commit()
            messagebox.showinfo("提示", f"数据表 {old_name} 已成功更名为 {new_name}!")
        except sqlite3.OperationalError as e:
            messagebox.showerror("错误", f"更改数据表名时出错: {str(e)}")
    table_dropdown['values'] = fetch_tables()
#修改数据表名界面
def rename_table_ui():
    selected_table = table_dropdown.get()
    if not selected_table or selected_table == "请选择数据表":
        messagebox.showwarning("提示", "请先选择一个数据表")
        return
    
    def execute_rename():
        new_table_name = rename_entry.get()
        if not new_table_name:
            messagebox.showwarning("提示", "新表名不能为空!")
            return
        rename_table(selected_table, new_table_name)
        rename_window.destroy()
        # 刷新下拉菜单
        table_names = fetch_tables()
        table_dropdown['values'] = table_names
        table_dropdown.set(new_table_name)
        update_display(new_table_name)
    
    rename_window = tk.Toplevel(window)
    rename_window.title("更改数据表名")
    rename_window.geometry("350x250")  # 设置窗口大小
    
    rename_label = ttk.Label(rename_window, text="新的数据表名:")
    rename_label.pack(pady=20)
    
    rename_entry = ttk.Entry(rename_window, width=30)
    rename_entry.pack(pady=10)
    rename_entry.insert(0, selected_table)

    # 增加按钮框架以容纳两个按钮
    button_frame = ttk.Frame(rename_window)
    button_frame.pack(pady=20)
    
    confirm_btn = ttk.Button(button_frame, text="确认", command=execute_rename, width=10)
    confirm_btn.grid(row=0, column=0, padx=10)

    cancel_btn = ttk.Button(button_frame, text="取消", command=rename_window.destroy, width=10)
    cancel_btn.grid(row=0, column=1, padx=10)

#删除数据表中的字段
def delete_column(table_name, column_to_delete):
    # 获取当前表的结构
    columns = fetch_structure(table_name)

    # 如果要删除的列不在表中，直接返回
    if column_to_delete not in columns:
        return

    # 从列列表中移除要删除的列
    columns.remove(column_to_delete)

    # 创建一个新的临时表，没有要删除的列
    new_table_name = table_name + "_new"
    with sqlite3.connect('sql.db') as conn:
        filtered_columns = [col for col in columns if col]  # 确保没有空的项
        conn.execute(f"CREATE TABLE {new_table_name} ({', '.join(filtered_columns)})")
        
        # 复制旧表的数据到新表中
        conn.execute(f"INSERT INTO {new_table_name} SELECT {', '.join(columns)} FROM {table_name}")

        # 删除旧表
        conn.execute(f"DROP TABLE {table_name}")

        # 将新表重命名为旧表的名称
        conn.execute(f"ALTER TABLE {new_table_name} RENAME TO {table_name}")

        conn.commit()

#删除数据结构
def delete_column_from_table(table_name, column_to_delete):
    # 获取数据表的所有列
    columns = fetch_structure(table_name)
    # 移除要删除的列
    columns.remove(column_to_delete)
    new_columns = ', '.join(columns)

    # 创建一个新的临时数据表，并从原始数据表中复制数据
    with sqlite3.connect('sql.db') as conn:
        new_table_name = table_name + "_temp"
        conn.execute(f"CREATE TABLE {new_table_name} AS SELECT {new_columns} FROM {table_name}")
        conn.execute(f"DROP TABLE {table_name}")
        conn.execute(f"ALTER TABLE {new_table_name} RENAME TO {table_name}")
        conn.commit()

    update_display()  # 更新显示的数据

  #编辑数据结构中的新增 字段UI  
def add_new_column_ui(selected_table):
    def submit():
        column_name = column_name_entry.get()
        column_type = column_type_dropdown.get()

        if not column_name or not column_type:
            messagebox.showwarning("提示", "字段名和类型都不能为空!")
            return

        try:
            add_new_column(selected_table, column_name, column_type)
            messagebox.showinfo("提示", f"字段 {column_name} 已成功添加!")
        except Exception as e:
            messagebox.showerror("错误", f"添加字段时出错: {str(e)}")

        add_column_window.destroy()
        update_display()

    add_column_window = tk.Toplevel(window)
    add_column_window.title("新增字段")

    ttk.Label(add_column_window, text="字段名:", font=("Arial", 12)).pack(pady=15)

    column_name_entry = ttk.Entry(add_column_window, font=("Arial", 12), width=30)
    column_name_entry.pack(pady=10, padx=20)

    ttk.Label(add_column_window, text="字段类型:", font=("Arial", 12)).pack(pady=15)

    column_types = ["INTEGER", "TEXT", "REAL", "BLOB", "VARCHAR(255)"]
    column_type_dropdown = ttk.Combobox(add_column_window, values=column_types, font=("Arial", 12))
    column_type_dropdown.set(column_types[0])
    column_type_dropdown.pack(pady=10, padx=20)

    action_frame = ttk.Frame(add_column_window)
    action_frame.pack(pady=20)

    ttk.Button(action_frame, text="新增", command=submit).pack(side="left", padx=60)
    ttk.Button(action_frame, text="关闭", command=add_column_window.destroy).pack(side="right", padx=60)

    add_column_window.mainloop()

#新增数据 界面
def add_new_column(table_name, column_name, column_type):
    with sqlite3.connect('sql.db') as conn:
        conn.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}")
        conn.commit()
def edit_or_add_row():
    selected_table = table_dropdown.get()
    if not selected_table or selected_table == "请选择数据表":
        messagebox.showwarning("提示", "请先选择一个数据表")
        return

    def submit_changes():
        values = [entry.get() for entry in entries]
        columns = fetch_structure(selected_table)
        query = f"INSERT OR REPLACE INTO {selected_table} ({', '.join(columns)}) VALUES ({', '.join(['?']*len(columns))})"
        with sqlite3.connect('sql.db') as conn:
            conn.execute(query, values)
            conn.commit()
        update_display()
        edit_row_window.destroy()

    edit_row_window = tk.Toplevel(window)
    edit_row_window.title("新增数据行")
    
    columns = fetch_structure(selected_table)
    entries = []
    for column in columns:
        frame = ttk.Frame(edit_row_window)
        frame.pack(fill=tk.X, padx=10, pady=5)
        label = ttk.Label(frame, text=f"{column}:")
        label.pack(side=tk.LEFT, padx=5)
        entry = ttk.Entry(frame)
        entry.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
        entries.append(entry)

    action_frame = ttk.Frame(edit_row_window)
    action_frame.pack(pady=20)
    submit_btn = ttk.Button(action_frame, text="提交", command=submit_changes)
    submit_btn.pack(side=tk.LEFT, padx=10)
    cancel_btn = ttk.Button(action_frame, text="取消", command=edit_row_window.destroy)
    cancel_btn.pack(side=tk.LEFT, padx=10)

#删除数据
def delete_row(item, identifier):
    selected_table = table_dropdown.get()
    col_names = fetch_structure(selected_table)
    with sqlite3.connect('sql.db') as conn:
        conn.execute(f"DELETE FROM {selected_table} WHERE {col_names[0]} = ?", (identifier,))
        conn.commit()

    tree.delete(item)

# 设置窗口大小
window.geometry("800x600")  # 调整窗口大小
frame = ttk.Frame(window, padding=(10, 5))
frame.pack(pady=20, padx=20, expand=True, fill='both')

table_names = fetch_tables()
table_dropdown = ttk.Combobox(frame, values=fetch_tables(), width=30)
table_dropdown.set("请选择数据表")
table_dropdown.grid(row=0, column=0, pady=10, padx=10, sticky='ew')
table_dropdown.bind("<<ComboboxSelected>>", display_data)
table_dropdown.bind("<<ComboboxSelected>>", on_table_selected)  # 显示编辑按钮
# 初始化编辑数据结构的按钮，但不显示
edit_structure_btn = ttk.Button(frame, text="编辑数据结构", command=edit_structure)
create_table_btn = ttk.Button(frame, text="创建新数据表", command=create_new_table)
rename_table_btn = ttk.Button(frame, text="编辑数据表名", command=rename_table_ui)
edit_row_btn = ttk.Button(frame, text="新增数据行", command=edit_or_add_row)
delete_table_btn = ttk.Button(frame, text="删除数据表", command=delete_table)
create_table_btn.grid(row=0, column=1, pady=10, padx=10)
delete_table_btn.grid(row=0, column=2, pady=10, padx=10)

# 初始化滚动条
vsb = ttk.Scrollbar(frame, orient="vertical")
hsb = ttk.Scrollbar(frame, orient="horizontal")

# 将滚动条与frame关联，并设置位置
vsb.grid(row=1, column=6, sticky='ns')
hsb.grid(row=2, column=0, columnspan=6, sticky='ew')

# 初始的提示
tree = ttk.Treeview(frame, columns=["提示"], show="headings", height=30, yscrollcommand=vsb.set, xscrollcommand=hsb.set)  
tree.heading("提示", text="提示")
tree.insert("", "end", values=["请选择一个数据库表"],tags=('notclickable',))
tree.grid(row=1, column=0, columnspan=6, pady=10, padx=10, sticky='ewns')  # 修改 数据框

# 将Treeview与滚动条关联
vsb.config(command=tree.yview)
hsb.config(command=tree.xview)

tree.bind('<<TreeviewSelect>>', on_tree_select)

# 为了使滚动条能随鼠标滚动，可以绑定MouseWheel事件
tree.bind('<MouseWheel>', lambda event: tree.yview_scroll(-1*(event.delta//120), "units"))

# 设置列的权重，使其可调整大小
frame.columnconfigure(0, weight=1)

window.mainloop()