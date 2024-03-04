#csvからデータを読み込む際に仕様
#csvはstrなので，データ送信時にtypeを付ける必要がある
#第1返り値を変換後データ，第2返り値をエラー文
import dateutil.parser
import datetime
from ipaddress import ip_interface

utc  = str(datetime.datetime.now())
datas = {"utc":"\x021048FH42022/11/03", "A":"4.5", "IP":"169.254.124.178/16", "B":"B"}

def TYPE_CHANGE(datas_):
    error_code = None
    datas_key = datas_.keys()
    for data_key in datas_key:
        try:
            datas_[data_key] = int(datas_[data_key])
        except ValueError:
            try:
                datas_[data_key] = float(datas_[data_key])
            except ValueError:
                try:
                    #時間に変換#4.5などの数値も時間型に変換するためintとfloatの後ろに配置
                    datas_[data_key] = dateutil.parser.parse(datas_[data_key])
                except ValueError:
                        pass
                except Exception as error_code:
                    break
            except Exception as error_code:
                break
        except Exception as error_code:
            break
        #print(str(datas_[data_key])+ ":" + str(type(datas_[data_key])))
    return datas_, error_code

a = TYPE_CHANGE(datas)