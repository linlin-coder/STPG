import os,sys,re
import glob
from public_method import *

from pytablewriter import MarkdownTableWriter,LatexTableWriter,HtmlTableWriter
# import markdown

patc = re.compile('^column\d+')
patn = re.compile('\d+$')

class Test():
    pass

class QC_Method():
    def __init__(self, toconfig, Name):
        self.toconfig = toconfig
        self.Name = Name
        self.MarkSign = {}
        self.QC_Result = ''
        self.table_markdown = HtmlTableWriter()# MarkdownTableWriter()

        # print(dir(self.table_markdown))

    def BuildObject(self, OneTaget):
        parser_format_list = self.toconfig.sign.qc_sign.strip().split("|")
        taget_content_list = OneTaget.strip().split("|")
        self.taget_content = Dict2Obj(dict(zip(parser_format_list, taget_content_list)))

        mark_list = self.toconfig.sign.qualify.strip().split("|")
        for markone in mark_list:
            markkey, markvalue = markone.split(":")
            try:
                self.MarkSign[eval(markkey)] = markvalue
            except:
                self.MarkSign[markkey] = markvalue

    def QC_Content(self):
        if self.taget_content.Type == 'file':
            if self.taget_content.Order == 'exist':
                if os.path.exists(self.taget_content.Path):
                    self.DefinedOutput(self.MarkSign[True])
                else:
                    self.DefinedOutput(self.MarkSign[False])
        elif self.taget_content.Type == 'table':
            table_markdown = self.table_markdown
            if not os.path.exists(self.taget_content.Path):
                self.DefinedOutput(self.MarkSign[False])
                return
            OrderDict = self.TableRule()
            TableJudged = []
            with open(self.taget_content.Path, 'r') as F_file:
                filecontent = F_file.readlines()
                table_markdown.table_name = self.taget_content.Name
                table_markdown.headers = filecontent[0].split("\t") + ['Judge']
                # TableJudged.append(TableHead)
                for line in filecontent[1:]:
                    tag = True
                    for ele_index, element in enumerate(line.strip().split('\t')):
                        if not tag:continue
                        if ele_index in OrderDict:
                            element = re.split('[;\|/]', element)[0].strip("%")
                            express_now = element+OrderDict[ele_index]
                            try:
                                express_result = eval(express_now)
                                if not express_result:
                                    tag = False
                            except Exception as e:
                                    print('expression is error:',express_now)
                                    tag = False
                    TableJudged.append(line.strip().split('\t')+[self.MarkSign[tag]])
                table_markdown.value_matrix = TableJudged
            self.DefinedOutput('\n\n'+table_markdown.dumps().replace("table", 'table border="1" '))

        elif self.taget_content.Type == 'list':
            if glob.glob(self.taget_content.Path) == []:
                self.DefinedOutput(self.MarkSign[False])
            else:
                self.DefinedOutput(self.MarkSign[True])
        elif self.taget_content.Type == 'xlsx':
            self.DefinedOutput(self.MarkSign[True])

    def DefinedOutput(self, result):
        if not result or (result==self.MarkSign[True] and self.taget_content.Type == 'file'):
            self.QC_Result = ''
            return
        self.QC_Result = '{filename} - {path} - {Order} - {result}  \n'.format(
            filename=self.taget_content.Name,
            path=self.taget_content.Path,
            Order=self.taget_content.Order,
            result=result
        )

    def TableRule(self):
        expredict = {}
        OrderList = self.taget_content.Order.split(',')
        for Order in OrderList:
            OrderSearch = patc.search(Order)
            if OrderSearch:
                column = int(patn.search(OrderSearch.group(0)).group(0)) - 1
                expression = Order[OrderSearch.span()[1]:]
                if column not in expredict:
                    expredict[column] = expression
        return expredict
