# Load HTML template
htmlTemplateFile = open("/lib/index.html", "r")
htmlTemplate = htmlTemplateFile.read()
htmlTemplateFile.close()

def generateHTMLOptions(optionsList):
    options = ""
    for i in optionsList:
        options += "<option value=\"" + i + "\">" + i + "</option>"
    return options

def generateIndexHTMLString(startupAnimation, startupAnimationChoices, error):
    step3 = htmlTemplate.replace("{{startupAnimation}}", startupAnimation)
    step4 = step3.replace("{{startupAnimationChoices}}", generateHTMLOptions(startupAnimationChoices))
    if error == False:
        return step4
    else:
        step5 = step4.replace("<div class=\"flex-item error-box\" style=\"display: none;\">", "<div class=\"flex-item error-box\" style=\"display: block;\">")
        step6 = step5.replace("{{errorText}}", error)
        return step6
