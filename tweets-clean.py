import sys
import csv
import re

reload(sys)
sys.setdefaultencoding('utf8')


def remove_stopwords(text):
    text = " " + text + " "

    p_longation = re.compile(ur'(.)\1+')

    arabic = open('stopwords.txt', 'rb')  # directory to stop words files goes here
    search = arabic.readlines()
    for i in range(0, len(search)):
        search[i] = search[i].replace("\n", "")
        text = text.replace(" " + search[i] + " ", " ")

    return text.strip()


def clean_str(text):
    text = " " + text + " "
    text = text.decode('utf-8', 'ignore')
    search = ["أ", "إ", "آ", "ة", "_", "-", "/", ".", "،", " و ", " يا ", '"', "ـ", "'", "ى", "\\"]
    replace = ["ا", "ا", "ا", "ه", " ", " ", "", "", "", " و", " يا", "", "", "", "ي", ""]

    for i in range(0, len(search)):
        text = text.replace(search[i], replace[i])

    # replace links
    p_links = re.compile(ur'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')
    subst = ur"WEB___LINK"
    text = re.sub(p_links, subst, text)

    p_hashtag = re.compile(ur"@(\w+)")
    subst = ur"MEN@TION"
    text = re.sub(p_hashtag, subst, text)

    text = text.strip()
    return text


target = open('clean_train_5.csv', 'w') #write clean data to a csv
target.truncate()

pos = []
neg = []
with open('lex.csv', 'rb') as csvfile:
    lex = csv.reader(csvfile, delimiter=',', quotechar='|')
    for line in lex:
        senti = line[0].split()
        if senti[1] == 'positive' or senti[1] == 'compound_pos':
            pos.append(senti[0])
        else:
            neg.append(senti[0])

with open('NU_EG_Twitter_corpus_train.csv', 'rb') as csvfile:  # corpus file goes here
    reader = csv.reader(csvfile, delimiter=',', quotechar='|')
    line_no = 0

    for row in reader:
        noPos = 0
        noNeg = 0
        noNeu = 0
        mention = 0
        link = 0
        # fields = row.split(",")
        if (line_no > 0):
            row[1]
            if len(row[1]) == 70:
                l = 1
            elif len(row[1]) < 70:
                l = 0
            else:
                l = 2
            row[1] = remove_stopwords(row[1])
            words = row[1].split()
            if "MEN@TION" in words:
                mention = 1
            if "WEB___LINK" in words:
                link = 1
            for char in words:
                if char in pos:
                    noPos += 1

                elif char in neg:
                    noNeg += 1

                else:
                    noNeu += 1
            row[1] = clean_str(row[1])
            target.write(row[0] + ",'" + row[1] + "'," + str(l) + "," + str(mention) + "," + str(link) + "," + str(
                noPos) + "," + str(noNeg) + "," + str(noNeu) + "," + row[2] + '\n')
        else:
            target.write("id,tweet,length,mention,link,positive,negative,Neutral,class\n")

        line_no += 1
    target.close()

