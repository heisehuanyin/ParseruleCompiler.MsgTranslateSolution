#/usr/bin/env python3
# -*- coding:utf-8 -*-

import sys
import xml.dom.minidom as elmtree

# 命令行参数形式
# compiler.py /source Source.parserule /out xx.xml
if sys.argv[1] == "/help":
    print("""
    翻译parserule文件为parseconfigeration文件,只接受以下形式命令行参数，错一个都不行
    命令行参数模式：
        program /help:打印帮助信息
        program /source source.parserule /out xx.xml :翻译parserule文件为parseconfigeration文件""");
    exit(0)

if len(sys.argv) != 5 or "/source" != sys.argv[1] or "/out" != sys.argv[3]:
    print("参数传递错误！")
    exit(0)
fileOut = sys.argv[4]

fileSymboIn = open(sys.argv[2], encoding="GBK")
lines = fileSymboIn.readlines()

docSymbo = elmtree.Document()

protocolNode = docSymbo.createElement("protocol")
docSymbo.appendChild(protocolNode)

softConfig = docSymbo.createElement("sysConfig")
protocolNode.appendChild(softConfig)
parseRule = docSymbo.createElement("parseRule")
protocolNode.appendChild(parseRule)

libraryContainer = docSymbo.createElement("library")
softConfig.appendChild(libraryContainer)
cmdlistNode = docSymbo.createElement("cmdlist")
softConfig.appendChild(cmdlistNode)
patternNode = docSymbo.createElement("pattern")
softConfig.appendChild(patternNode)

# 整理所有的行内容，将注释和转义字符去除
for line in lines:
    index = lines.index(line)
    if "#" in line:
        line = line[0:line.find("#")]
    if "\t" in line:
        line = line.replace('\t', "")
    if "\n" in line:
        line = line.replace('\n', "")

    lines[index] = line

# 寻找系统基础支持包，需要判断是否存在此配置，如果不存在该包的处理情况
for line in lines:
    if line.startswith("."):
        baseSupport = docSymbo.createElement('baseSupport')
        baseSupport.setAttribute('rel', line[1:])
        libraryContainer.appendChild(baseSupport)
        pass

if not baseSupport:
    print("未定义基础解析支持包，请重新配置%s文件", sys.argv[2])
    exit(0)


# 整理配置文件中所用到的引入库，还有所用到的命令
for line in lines:
    if line.startswith(">"):
        words = line[1:].split(":")
        if words[1].split(" ")[0] == baseSupport.getAttribute("rel"):
            pass
        else:
            for apNode in docSymbo.getElementsByTagName("enhance"):
                if apNode.getAttribute("rel") == words[1].split(" ")[0]:
                    break
            else:
                enhanceNode = docSymbo.createElement("enhance")
                enhanceNode.setAttribute("rel", words[1].split(" ")[0])
                libraryContainer.appendChild(enhanceNode)

        cmdNode = docSymbo.createElement(words[0])
        cmdNode.setAttribute("rel", words[1])
        cmdlistNode.appendChild(cmdNode)
        pass

# 整理整份解析协议中用到的判据链条
for line in lines:
    if line.startswith("::"):
        abssss = line[2:].split(",")
        for aa in abssss:
            if not cmdlistNode.getElementsByTagName(aa):
                print("存在未知的标识符:", aa)
                exit(0)
            else:
                judgeMentList = abssss

if not judgeMentList:
    print("未形成完整判据，请检查parserule文件")
    exit(0)

# 正式的解析规则配置，与适配模式的整理
for line in lines:
    if line.startswith("\""):
        sections0 = line[0:line.find(":")]
        sections1 = line[line.find(":")+1:]
        # section0
        jj = sections0.replace("\"", "")
        if protocolNode.getElementsByTagName("parseRule").length != 0:
            parseRule = protocolNode.getElementsByTagName("parseRule")[0]
        for itNode in judgeMentList:  # 构建一条判据链条，填充判据信息
            for nadNode in parseRule.getElementsByTagName(itNode):
                if nadNode.getAttribute("value") == str(jj.split(",")[judgeMentList.index(itNode)]):
                    parseRule = nadNode
                    break
            else:
                oNode = docSymbo.createElement(itNode)
                oNode.setAttribute("value", str(jj.split(",")[judgeMentList.index(itNode)]))
                parseRule.appendChild(oNode)
                parseRule = oNode

        # section1 构建每条总线消息的详细解析规则，提取匹配模式未知信息
        wWords = sections1.split(",")  # 清洗不和谐因素
        for word in wWords:
            cc = wWords.index(word)
            if "[" in word:
                word = word.replace("[", "")
            if "]" in word:
                word = word.replace("]", "")
            wWords[cc] = word
            pass

        for word in wWords:  # 构建每单元解析规则
            cc = wWords.index(word)
            name = "nor"
            if ":" in word:
                name = word[0:word.find(":")]
                word = word[word.find(":")+1:]
            if not cmdlistNode.getElementsByTagName(word):
                continue  # 命令未注册，忽略

            parseUnit = docSymbo.createElement(word)
            parseUnit.setAttribute("index", str(cc))
            if name == "nor":
                parseUnit.setAttribute("name", "default")
            else:
                parseUnit.setAttribute("name", name)
            parseRule.appendChild(parseUnit)
            pass

        if softConfig.getElementsByTagName("pattern").length != 0:
            patternNode = softConfig.getElementsByTagName("pattern")[0]
        for jmt in judgeMentList:  # 构建匹配模式信息
            tmpNode = cmdlistNode.getElementsByTagName(jmt)[0]
            attr_ahead = tmpNode.getAttribute("rel").split(" ")[0]
            if attr_ahead == baseSupport.getAttribute("rel"):
                for nNode in patternNode.getElementsByTagName(jmt):
                    if nNode.getAttribute("index") == "not":
                        patternNode = nNode
                        break
                else:
                    fitNode = docSymbo.createElement(jmt)
                    fitNode.setAttribute("index", "not")
                    patternNode.appendChild(fitNode)
                    patternNode = fitNode
                continue

            for word in wWords:
                cc = wWords.index(word)
                if ":" in word:
                    name = word[0:word.find(":")]
                    word = word[word.find(":")+1:]
                if word == jmt:
                    for nbNode in patternNode.getElementsByTagName(word):
                        if nbNode.getAttribute("index") == str(cc):
                            patternNode = nNode
                            break
                    else:
                        fitNode = docSymbo.createElement(word)
                        fitNode.setAttribute("index", str(cc))
                        patternNode.appendChild(fitNode)
                        patternNode = fitNode
                    break
            else:
                print("未找到匹配判据链信息，请重新检查parserule文件，行号：", lines.index(line) + 1)
                exit(0)

# 配置文件写出
f = open(fileOut, 'w', encoding="gbk")
f.write(docSymbo.toprettyxml(indent=''))
f.close()
fileSymboIn.close()
pass
