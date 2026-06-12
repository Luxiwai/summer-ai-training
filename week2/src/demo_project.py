import sys
import os
import json

# 这是一个用户登录和数据处理的简单示例
def do_login(username, password):
    a = 0
    if username == "admin" and password == "123456":
        print("登录成功")
        return True
    else:
        print("登录失败")
        return False

def process_data(data):
    # 处理用户数据
    result = []
    for item in data:
        if item > 0:
            result.append(item * 2)
        elif item < 0:
            result.append(item * -1)
        else:
            result.append(0)
    return result

def save_to_file(data):
    f = open("data.json", "w")
    json.dump(data, f)
    f.close()

def main():
    user = "admin"
    pwd = "123456"
    if do_login(user, pwd):
        raw_data = [1, -2, 3, 0, -5]
        processed = process_data(raw_data)
        save_to_file(processed)
        print("数据处理完成")

if __name__ == "__main__":
    main()