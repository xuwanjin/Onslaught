# encoding: utf-8

import os
import subprocess
import sys
import threading
import time

import Utils
from Device import Android_Device

adb_devices_cmd = "adb devices"
current_test_package = ""


def get_log_catcher_package():
    with open(file="./log_catcher.ini") as f:
        for line in f:
            stripLine = str(line).replace("\n", "")
            if stripLine.__contains__("log_catcher_package"):
                package_name = stripLine.split("=")[1]
                return package_name.replace("\"", "").strip()

    return "log_catcher_directory"


def is_only_catch_app_log():
    with open(file="./log_catcher.ini") as f:
        for line in f:
            stripLine = str(line).replace("\n", "")
            if stripLine.__contains__("is_only_catch_app_log"):
                package_name = stripLine.split("=")[1]
                if package_name.replace("\"", "").strip().__eq__("True"):
                    return True

    return False


def get_system_encoding():
    return sys.getdefaultencoding()


def get_device():
    adb_devices_result = subprocess.getstatusoutput(adb_devices_cmd)
    print("list all android device: " + str(adb_devices_result))
    device_dict = {}
    if adb_devices_result[0] == 0:
        split_result = adb_devices_result[1].split("\n")
        devices_list = split_result[1:split_result.__len__() - 1]
        for devices_id_record in devices_list:
            serial = devices_id_record.split("\t")[0]
            is_online = devices_id_record.split("\t")[1]
            key_is_online = True
            if is_online.__contains__("offline"):
                key_is_online = False

            android_device_ = Utils.get_device_info(serial, key_is_online)

            device_dict[android_device_.device_serial] = android_device_
    return device_dict


def catch_device_log(device: Android_Device, package_name: str):
    if not device.isOnline():
        return
    """
    再次检查一下设备是否在线
    """
    realTimeDevice = get_device()[device.device_serial]
    print("check the device is online: " + str(realTimeDevice.isOnline()))
    if not realTimeDevice.isOnline():
        return

    # log 的路径  包名 /  日期
    current_test_date = time.strftime("%Y-%m-%d_%H", time.localtime())
    print("the current test date: " + str(current_test_date))
    current_path = os.getcwd()
    """
     路径保持为 包名/设备model名称/设备的device_serial/当前日期的+ 小时.log
    """
    log_path = current_path + os.sep + package_name + os.sep + device.model + os.sep + device.device_serial

    if not os.path.exists(log_path):
        os.makedirs(log_path)

    log_file_path = log_path + os.sep + current_test_date + ".log"

    print("the log path which we want to save: " + log_file_path)
    logcat_cmd = "adb -s " + realTimeDevice.device_serial + " logcat -b all"
    encoding = get_system_encoding()
    log_file = open(log_file_path, "w", encoding=encoding)
    result = subprocess.Popen(logcat_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    line_list = list()
    print("the encoding of the system = " + encoding)
    for line in iter(result.stdout.readline, "b"):
        current_date = time.strftime("%Y-%m-%d_%H", time.localtime())
        if current_date.__eq__(current_test_date):
            lineStr = line.decode(encoding, "ignore")
            stripLine = lineStr.replace("\n", "") + "\n"
            if stripLine.__eq__("\n"):
                pass
            else:
                line_list.append(stripLine)
                if line_list.__len__() > 5000:
                    log_file.writelines(line_list)
                    log_file.flush()
                    line_list.clear()

        else:
            print("进入下一个小时的, 收集手机 log 的阶段")
            catch_device_log(device, package_name)


if __name__ == '__main__':
    all_device_dict = get_device()
    current_test_package = get_log_catcher_package()
    print("the log save path is: " + current_test_package)
    for adb_device in all_device_dict.values():
        print("============= " + str(adb_device))
        device_thread = threading.Thread(target=catch_device_log,
                                         args=(adb_device, current_test_package))
        device_thread.start()
