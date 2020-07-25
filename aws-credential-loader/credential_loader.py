import warnings
import os
warnings.filterwarnings("ignore")
import time
from selenium.webdriver import Firefox


def getAWSCredentials(awsEmail, awsPassword):
    driver = Firefox()
    driver.get('https://www.awseducate.com/signin/SiteLogin')
    driver.find_element_by_name("loginPage:siteLogin:loginComponent:loginForm:username").send_keys(awsEmail)
    driver.find_element_by_name("loginPage:siteLogin:loginComponent:loginForm:password").send_keys(awsPassword)
    sign_in_button = driver.find_element_by_class_name("loginText")
    time.sleep(1)
    sign_in_button.click()
    time.sleep(7)
    aws_account = driver.find_elements_by_xpath("//a[@class='hdNavTop']")[4]
    aws_account.click()
    time.sleep(5)
    account = driver.find_element_by_class_name("btn")
    account.click()
    currentTab = driver.current_window_handle
    time.sleep(20)
    vocareum_tab = driver.window_handles[1]
    driver.switch_to.window(vocareum_tab)
    account_details = driver.find_element_by_id("showawsdetail")
    account_details.click()
    time.sleep(4)
    clickey_btn = driver.find_element_by_id("clikeyboxbtn")
    clickey_btn.click()
    time.sleep(3)
    span_tags = driver.find_elements_by_tag_name("span")
    for tag in span_tags:
        if '[default]' in tag.text:
            text = tag.text
            return driver,text


if __name__ == "__main__":
    awsEmail = "rthiruvo@asu.edu"
    awsPassword = "Raghav@13"
    repeatDuration = 60*45
    retryTime = 60*15

    cnt = 0
    lastUpdateTime = 0
    while True:
        if (time.time() - lastUpdateTime) > repeatDuration:
            try:
                driver.quit()
            except:
                pass
            cnt += 1
            print("Executing {} time".format(cnt))
            driver, content = getAWSCredentials(awsEmail, awsPassword)
            values = [v.strip() + '\n' for v in content.split()]
            file = open("/Users/moudhgn/.aws/credentials", "w")
            file.writelines(values)
            file.close()
            print("Done writing")
            print("Transferring to ec2")
            ret = os.system("cd ../checklist-skill && bash cred_transfer.sh")
            if ret >= 0:
                print("Done")
            else:
                print("Failed")
            lastUpdateTime = time.time()
        else:
            time.sleep(retryTime)
