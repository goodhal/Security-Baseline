import os
import re
import sys
sys.path.append('../../')
from common.baseline_fix import GenFixScript
from common.baseline_param_parse import BaselineParamParse


class GenTomcatFixScript(GenFixScript):
    def __init__(self,ip_addr):
        baseline_type = "Tomcat"
        super().__init__(ip_addr,baseline_type)

    def gen_shell_script_usage(self):
        self.shell_script_obj.writelines("""
usage(){
  echo "
Usage:
  -d, --basedir     mysql security config path to save, default /opt/apache-tomcat-8.5.35
  -h, --help        display this help and exit

  example1: bash tomcat_baseline_fix.sh -d/opt/apache-tomcat-8.5.35
  example2: bash tomcat_baseline_fix.sh --basedir=/opt/apache-tomcat-8.5.35
"
}

main_pre(){
    # set -- $(getopt i:p:h "$@")
    set -- $(getopt -o d:h --long basedir:,help -- "$@")
    ipaddr=`ifconfig|grep 'inet'|grep -v '127.0.0.1'|awk '{print $2}'|cut -d':' -f 2`
    id=0
    CATALINA_HOME='/opt/apache-tomcat-8.5.35'

    while true
    do
      case "$1" in
      -d|--basedir)
          CATALINA_HOME="$2"
          shift
          ;;
      -h|--help)
          usage
          exit
          ;;
      --)
        shift
        break
        ;;
      *)
        echo "$1 is not option"
        ;;
      esac
      shift
    done
    xml_file_name="/tmp/${ipaddr}_tomcat_fix.log"
}""")

    def gen_shell_script_delete_example_doc(self,fix_object,fix_comment,check_result):
        fix_command = "cd $CATALINA_HOME/webapps ;"
        for line in check_result:
            dir_name = line.split()[-1]
            fix_command += f"rm -rf {dir_name};"
        self.shell_script_obj.writelines("""
fixExampleDoc(){
    fix_object=\""""+fix_object+"""\"
    fix_comment=\""""+fix_comment+"""\"
    fix_command=\"""" + fix_command + """\"
    fix_result=`eval $fix_command`
    appendToXml "$fix_object" "$fix_command" "$fix_comment" "$fix_result"
}
        """)

    def gen_shell_script_disable_default_account(self,fix_object,fix_comment,check_result):
        fix_command = "cd $CATALINA_HOME/conf;"
        for user in check_result:
            tmp = user.replace("/","\/").replace("\"","\\\"")
            fix_command += f"sed -i 's/{tmp}/<!--{tmp}-->/' tomcat-users.xml ;"
        self.shell_script_obj.writelines("""
fixDefaultAccount(){
    fix_object=\"""" + fix_object + """\"
    fix_comment=\"""" + fix_comment + """\"
    fix_command=\"""" + fix_command + """\"
    fix_result=`eval $fix_command`
    appendToXml "$fix_object" "$fix_command" "$fix_comment" "$fix_result"
}
                """)

    def gen_shell_script_disable_list_dir(self,fix_object,fix_comment,check_result):
        item = check_result[0].replace("/","\/")
        value = check_result[1].replace("/","\/")

        correct_value = value.replace("true","false")
        correct_str = f"{item}{correct_value}"
        # fix_command = f"cd $CATALINA_HOME/conf; sed -i -r 's/{item}\s*{value}/{correct_str}/' web.xml"
        fix_command = f"cd $CATALINA_HOME/conf; sed -i '/"+item+"/{n;s/true/false/;}' web.xml"

        self.shell_script_obj.writelines("""
fixListDir(){
    fix_object=\"""" + fix_object + """\"
    fix_comment=\"""" + fix_comment + """\"
    fix_command=\"""" + fix_command + """\"
    fix_result=`eval $fix_command`
    appendToXml "$fix_object" "$fix_command" "$fix_comment" "$fix_result"
}
                """)

    def gen_shell_script_self_define_error_page(self,fix_object,fix_comment,check_result):
        fix_command = "cd $CATALINA_HOME/conf;"
        error_code_list_reg = "<error-code>\d+</error-code>"
        check_result_str = "\n".join(check_result)
        error_code_list = re.findall(error_code_list_reg,check_result_str)
        error_code_str = "、".join(error_code_list)

        web_label_close_reg = "^\s*<\/web-app>"

        for error_code in ("401","404","500"):
            if error_code not in error_code_str:
                fix_command += f"sed -i '/{web_label_close_reg}/i\\<error-page>\\n<error-code>{error_code}<\/error-code>\\n<location>{error_code}.htm<\/location>\\n<\/error-page>' web.xml;"
        self.shell_script_obj.writelines("""
fixErrorPage(){
    fix_object=\"""" + fix_object + """\"
    fix_comment=\"""" + fix_comment + """\"
    fix_command=\"""" + fix_command + """\"
    fix_result=`eval $fix_command`
    appendToXml "$fix_object" "$fix_command" "$fix_comment" "$fix_result"
}
                """)

    def gen_shell_script_enable_access_log(self,fix_object,fix_comment,check_result):
        host_label_close_reg = "\s*<\/Host>"
        fix_command = "cd $CATALINA_HOME/conf;"
        fix_command += f"sed -i '/{host_label_close_reg}/i\\<Valve className=\"org.apache.catalina.valves.AccessLogValve\" directory=\"logs\" prefix=\"localhost_access_log\" suffix=\".txt\" pattern=\"%h %l %u %t &quot;%r&quot; %s %b\" \/>' server.xml"
        self.shell_script_obj.writelines("""
fixEnableAccessLog(){
    fix_object=\"""" + fix_object + """\"
    fix_comment=\"""" + fix_comment + """\"
    fix_command=\"""" + fix_command + """\"
    fix_result=`eval $fix_command`
    appendToXml "$fix_object" "$fix_command" "$fix_comment" "$fix_result"
}
                """)

    def gen_shell_script_remove_server_number(self,fix_object,fix_comment,check_result):
        # server_info_reg = "server\.2_info=Apache\s*Tomcat\/[\d|.]{3,}"
        # server_number_reg = "server\.number=[\d|.]{3,}"
        number_reg = "[\d|.]{3,}"

        fix_command = "cd $CATALINA_HOME/lib ;"
        fix_command += "cp catalina.jar catalina.jar.bak ;"
        fix_command += "mkdir delete_number_dir ;"
        fix_command += "cd delete_number_dir ;"
        fix_command += "jar -xf ../catalina.jar ;"
        fix_command += f"sed -i -r 's/{number_reg}//g' org/apache/catalina/util/ServerInfo.properties ;"
        fix_command += "jar -cf ../catalina.jar *;"
        self.shell_script_obj.writelines("""
fixServerVersion(){
    fix_object=\"""" + fix_object + """\"
    fix_comment=\"""" + fix_comment + """\"
    fix_command=\"""" + fix_command + """\"
    fix_result=`eval $fix_command`
    appendToXml "$fix_object" "$fix_command" "$fix_comment" "$fix_result"
}
                """)

    def gen_shell_script_change_default_port(self,fix_object,fix_comment,check_result):
        fix_command = "cd $CATALINA_HOME/conf ;"
        fix_command += "sed -i -r 's/<Connector port=\"8080\"/<Connector port=\"9080\"/' server.xml"
        self.shell_script_obj.writelines("""
fixDefaultPort(){
    fix_object=\"""" + fix_object + """\"
    fix_comment=\"""" + fix_comment + """\"
    fix_command=\"""" + fix_command + """\"
    fix_result=`eval $fix_command`
    appendToXml "$fix_object" "$fix_command" "$fix_comment" "$fix_result"
}
                """)

    def gen_shell_script_non_root(self,fix_object,fix_comment,check_result):
        self.shell_script_obj.writelines("""
fixProcessRunner(){
    fix_object=\"""" + fix_object + """\"
    fix_comment=\"""" + fix_comment + """\"
    fix_command="cd $CATALINA_HOME/webapps &&rm -rf docs examples manager ROOT host-manager"
    fix_result=`eval $fix_command`
    appendToXml "$fix_object" "$fix_command" "$fix_comment" "$fix_result"
}
                """)


    def gen_shell_script_main_part(self):
        need_fix_item = self.node_xpath(self.html_obj.html, "//div[@class = 'card-header bg-danger text-white']/..")
        # need_fix_item = self.html_obj.html.xpath("//div[contains(@class, 'card-header')]/..")
        # all_need_fix_items = all_item_div.xpath("//div[@class='card-header bg-danger text-white']/..")
        # gg=self.soup.find_all(id="accordion2")
        for item in need_fix_item:
            check_title = self.text_xpath(item, "div//a")
            check_object = self.text_xpath(item, "div//table/tr[1]/td")
            check_command = self.text_xpath(item, "div//table/tr[2]/td")
            check_comment = self.text_xpath(item, "div//table/tr[3]/td")
            check_result = self.text_xpath(item, "div//table/tr[4]/td")
            if check_title == "删除示例文档":
                self.gen_shell_script_delete_example_doc(check_object,check_comment,check_result)
                self.fix_item_list["gen_shell_script_delete_example_doc"] = "fixExampleDoc"
                continue
            elif check_title == "禁用tomcat默认帐号":
                self.gen_shell_script_disable_default_account(check_object,check_comment,check_result)
                self.fix_item_list["gen_shell_script_disable_default_account"] = "fixDefaultAccount"
                continue
            elif check_title == "禁止列目录":
                self.gen_shell_script_disable_list_dir(check_object,check_comment,check_result)
                self.fix_item_list["gen_shell_script_disable_list_dir"] = "fixListDir"
                continue
            elif check_title == "自定义错误页面":
                self.gen_shell_script_self_define_error_page(check_object,check_comment,check_result)
                self.fix_item_list["gen_shell_script_self_define_error_page"] = "fixErrorPage"
                continue
            elif check_title == "开启访问日志":
                self.gen_shell_script_enable_access_log(check_object,check_comment,check_result)
                self.fix_item_list["gen_shell_script_enable_access_log"] = "fixEnableAccessLog"
                continue
            elif check_title == "隐藏版本号":
                self.gen_shell_script_remove_server_number(check_object,check_comment,check_result)
                self.fix_item_list["gen_shell_script_remove_server_number"] = "fixServerVersion"
                continue
            elif check_title == "修改默认监听端口":
                self.gen_shell_script_change_default_port(check_object,check_comment,check_result)
                self.fix_item_list["gen_shell_script_change_default_port"] = "fixDefaultPort"
                continue
            elif check_title == "不以root/admin用户运行程序":
                self.gen_shell_script_non_root(check_object,check_comment,check_result)
                self.fix_item_list["gen_shell_script_non_root"] = "fixProcessRunner"
        pass

    def gen_shell_script(self):
        self.gen_shell_script_head_part()
        self.gen_shell_script_main_part()
        self.gen_shell_script_usage()
        self.gen_shell_script_tail_part()



if __name__ == "__main__":
    bpp_obj = BaselineParamParse()
    model, ip = bpp_obj.param_parse(sys.argv[1:])
    # 如果指定ip模式
    if model == "ip":
        # 如果ip模式中未给出ip列出则报错退出
        if ip is None:
            bpp_obj.usage()
            sys.exit(1)
        else:
            ip_list = ip.split(",")
            for ip_addr in ip_list:
                # 如果指定的ip对应的文件并不存在则跳过
                if not os.path.exists(f"../4_report/{ip_addr}_tomcat_report.html"):
                    print(f'sorry, file "../4_report/{ip_addr}_tomcat_report.html" is not exist, it will be skip')
                    continue
                gen_fix_obj = GenTomcatFixScript(ip_addr)
                gen_fix_obj.gen_shell_script()
    # 如果指定文件夹模式
    elif model == "dir":
        argv = sys.argv[1:]
        ip_reg = "(\d{1,3}\.{1}){3}\d{1,3}"
        full_reg = f"{ip_reg}_tomcat_report\.html"
        pwd_file_list = os.listdir("../4_report")
        for file in pwd_file_list:
            if re.search(full_reg, file):
                ip_addr = re.search(ip_reg, file).group()
                gen_fix_obj = GenTomcatFixScript(ip_addr)
                gen_fix_obj.gen_shell_script()