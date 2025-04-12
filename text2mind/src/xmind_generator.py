"""
Module for generating XMind files from parsed text structure.
"""

import os
import tempfile
import shutil
import zipfile
import json
import uuid
import logging
from PIL import Image, ImageDraw, ImageFont
import time
import xml.sax.saxutils as saxutils

# 配置详细的日志记录
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(os.path.dirname(os.path.dirname(__file__)), "xmind_debug.log")),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("xmind_generator")

def create_xmind_from_structure(structure, output_path):
    """
    Create an XMind file from a hierarchical structure.
    
    Args:
        structure (dict): The hierarchical structure with 'title' and 'children' keys.
        output_path (str): The path where the XMind file will be saved.
        
    Returns:
        str: The path to the created XMind file.
    """
    logger.info(f"开始创建XMind文件: {output_path}")
    logger.info(f"结构根节点: {structure['title']}, 顶级子节点数: {len(structure.get('children', []))}")
    
    # 创建临时目录
    temp_dir = tempfile.mkdtemp()
    logger.debug(f"创建临时目录: {temp_dir}")
    
    try:
        # 创建必要的目录结构
        os.makedirs(os.path.join(temp_dir, 'META-INF'), exist_ok=True)
        os.makedirs(os.path.join(temp_dir, 'Thumbnails'), exist_ok=True)
        os.makedirs(os.path.join(temp_dir, 'attachments'), exist_ok=True)
        
        # 计算节点数量
        node_count = count_nodes(structure)
        logger.info(f"总节点数: {node_count}")
        
        # 根据节点数量选择布局策略
        layout_strategy = select_layout_strategy(node_count)
        logger.info(f"选择布局策略: {layout_strategy}")
        
        # 创建content.xml文件 - 使用新的优化实现
        content_xml_path = create_content_xml(temp_dir, structure, layout_strategy)
        logger.debug(f"content.xml 已创建: {content_xml_path}")
        
        # 创建标准格式的meta.xml
        meta_xml = """<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<meta xmlns="urn:xmind:xmap:xmlns:meta:2.0" version="2.0">
  <Creator>
    <n>XMind</n>
    <Version>22.11.3456.0</Version>
  </Creator>
</meta>"""
        
        meta_xml_path = os.path.join(temp_dir, 'meta.xml')
        with open(meta_xml_path, 'w', encoding='utf-8') as f:
            f.write(meta_xml)
        
        logger.debug(f"meta.xml 已写入到: {meta_xml_path}")
        
        # 创建标准manifest.xml
        manifest_xml = """<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<manifest xmlns="urn:xmind:xmap:xmlns:manifest:1.0">
  <file-entry full-path="content.xml" media-type="text/xml"/>
  <file-entry full-path="meta.xml" media-type="text/xml"/>
  <file-entry full-path="META-INF/" media-type=""/>
  <file-entry full-path="META-INF/manifest.xml" media-type="text/xml"/>
  <file-entry full-path="styles.xml" media-type="text/xml"/>
  <file-entry full-path="Thumbnails/" media-type=""/>
  <file-entry full-path="Thumbnails/thumbnail.png" media-type="image/png"/>
  <file-entry full-path="attachments/" media-type=""/>
  <file-entry full-path="attachments/padding.bin" media-type="application/octet-stream"/>
  <file-entry full-path="attachments/markers.xml" media-type="text/xml"/>
</manifest>"""
        
        manifest_xml_path = os.path.join(temp_dir, 'META-INF', 'manifest.xml')
        with open(manifest_xml_path, 'w', encoding='utf-8') as f:
            f.write(manifest_xml)
        
        logger.debug(f"manifest.xml 已写入到: {manifest_xml_path}")
        
        # 获取XMind官方样式文件
        styles_xml = get_xmind_pro_styles()
        
        styles_xml_path = os.path.join(temp_dir, 'styles.xml')
        with open(styles_xml_path, 'w', encoding='utf-8') as f:
            f.write(styles_xml)
        
        logger.debug(f"styles.xml 已写入到: {styles_xml_path}")
        
        # 创建缩略图
        create_thumbnail_image(structure, os.path.join(temp_dir, 'Thumbnails', 'thumbnail.png'))
        
        # 创建markers.xml文件
        markers_xml = """<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<marker-sheet xmlns="urn:xmind:xmap:xmlns:marker:2.0" version="2.0"/>"""
        
        markers_xml_path = os.path.join(temp_dir, 'attachments', 'markers.xml')
        with open(markers_xml_path, 'w', encoding='utf-8') as f:
            f.write(markers_xml)
        
        logger.debug(f"markers.xml 已写入到: {markers_xml_path}")
        
        # 创建大文件数据 - 针对大型思维导图的优化
        large_file_data = create_large_file_data(node_count)
        
        padding_path = os.path.join(temp_dir, 'attachments', 'padding.bin')
        with open(padding_path, 'wb') as f:
            f.write(large_file_data)
        
        logger.debug(f"padding.bin 已写入到: {padding_path}, 大小: {len(large_file_data)} 字节")
        
        # 打包为.xmind文件 (实际上是.zip格式)
        logger.info(f"将临时目录内容打包为XMind文件: {output_path}")
        
        # 如果目标目录不存在，创建它
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, temp_dir)
                    zipf.write(file_path, arcname)
        
        logger.info(f"XMind文件创建成功: {output_path}")
        
        return output_path
        
    except Exception as e:
        logger.error(f"创建XMind文件时出错: {e}", exc_info=True)
        try:
            return create_fallback_xmind(structure, output_path)
        except Exception as e2:
            logger.critical(f"创建备用XMind文件也失败: {e2}", exc_info=True)
            return None
            
    finally:
        # 清理临时目录
        try:
            shutil.rmtree(temp_dir)
            logger.debug(f"已清理临时目录: {temp_dir}")
        except Exception as e:
            logger.warning(f"清理临时目录时出错: {e}")

def create_blank_thumbnail(output_path, size=(128, 128)):
    """
    创建空白缩略图 - XMind需要这个文件存在
    
    Args:
        output_path (str): 输出路径
        size (tuple): 图像大小
    """
    try:
        # 创建一个简单的白色缩略图
        img = Image.new('RGB', size, color='white')
        img.save(output_path, format='PNG')
        logger.debug(f"空白缩略图创建成功: {output_path}")
    except Exception as e:
        logger.error(f"创建缩略图出错: {e}")
        # 如果PIL失败，尝试直接写入一个最小的PNG图像
        try:
            # 最小的有效PNG图像 (1x1 白色像素)
            minimal_png = (
                b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00'
                b'\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDAT'
                b'\x08\x99c\xf8\xff\xff?\x00\x05\xfe\x02\xfe\xdc\xcc\x59\xe7'
                b'\x00\x00\x00\x00IEND\xaeB`\x82'
            )
            with open(output_path, 'wb') as f:
                f.write(minimal_png)
            logger.debug(f"最小PNG缩略图创建成功: {output_path}")
        except Exception as e2:
            logger.error(f"创建最小PNG也失败: {e2}")

def create_xmind_zip_standard(source_dir, output_path):
    """
    使用标准的XMind ZIP结构创建文件
    
    Args:
        source_dir (str): 源目录
        output_path (str): 输出路径
    """
    logger.info(f"开始创建标准XMind ZIP文件: {output_path}")
    
    try:
        # 使用XMind标准压缩方式
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as zipf:
            # 添加文件 - 添加顺序很重要
            zipf.write(os.path.join(source_dir, 'META-INF', 'manifest.xml'), 'META-INF/manifest.xml')
            zipf.write(os.path.join(source_dir, 'content.xml'), 'content.xml')
            zipf.write(os.path.join(source_dir, 'meta.xml'), 'meta.xml')
            zipf.write(os.path.join(source_dir, 'styles.xml'), 'styles.xml')
            zipf.write(os.path.join(source_dir, 'Thumbnails', 'thumbnail.png'), 'Thumbnails/thumbnail.png')
            zipf.write(os.path.join(source_dir, 'attachments', 'markers.xml'), 'attachments/markers.xml')
            
            # 添加填充文件 - 确保文件足够大，XMind能显示所有内容
            for root, dirs, files in os.walk(os.path.join(source_dir, 'attachments')):
                for file in files:
                    if file != 'markers.xml':  # 已添加
                        file_path = os.path.join(root, file)
                        rel_path = os.path.relpath(file_path, source_dir)
                        zipf.write(file_path, rel_path)
                        
        logger.info(f"XMind ZIP文件创建成功: {output_path}")
        return True
    except Exception as e:
        logger.error(f"创建ZIP文件时出错: {e}", exc_info=True)
        return False

def count_nodes(structure):
    """计算结构中的节点总数"""
    if not structure:
        return 0
    
    # 检查结构类型并兼容旧版API
    children = []
    if isinstance(structure, dict):
        # 兼容两种字段格式
        if 'children' in structure:
            children = structure['children']
        elif 'topics' in structure:
            children = structure['topics']
            
    return 1 + count_nodes_recursive(children)

def count_nodes_recursive(nodes):
    """递归计算节点总数"""
    if not nodes:
        return 0
    
    count = len(nodes)
    
    for node in nodes:
        # 兼容两种字段格式
        children = []
        if isinstance(node, dict):
            if 'children' in node:
                children = node['children']
            elif 'topics' in node:
                children = node['topics']
        
        count += count_nodes_recursive(children)
    
    return count

def select_layout_strategy(node_count):
    """根据节点数量选择最优布局策略"""
    if node_count <= 100:
        return "map"  # 小型图使用普通思维导图布局
    elif node_count <= 1000:
        return "logic.right"  # 中型图使用逻辑布局
    elif node_count <= 5000:
        return "tree.right"  # 大型图使用树状布局
    elif node_count <= 10000:
        return "logic.right"  # 大型图使用逻辑右布局
    else:
        return "org.xmind.ui.fishbone.leftHeaded"  # 超大型图使用鱼骨图布局，XMind展示效果更好

def create_large_file_data(node_count):
    """
    创建足够大的数据文件，确保XMind显示全部内容
    
    Args:
        node_count (int): 节点数量
    """
    # 创建随机数据文件，大小和节点数量成正比，至少2MB
    data_size = max(2 * 1024 * 1024, node_count * 500)  # 增加到每节点500字节
    
    # 创建随机数据
    return os.urandom(data_size)

def generate_topic_xml_optimized(topics, parent_id, layout_strategy, level=1):
    """
    优化的主题XML生成函数，避免内存溢出
    使用分块的方式处理主题，每块最多处理1000个主题
    
    Args:
        topics (dict): 主题字典
        parent_id (str): 父主题ID
        layout_strategy (str): 布局策略
        level (int): 当前层级，用于缩进
        
    Returns:
        str: 生成的XML字符串
    """
    chunks = []
    
    if not topics:
        return ""
    
    # 处理当前主题
    topic_title = topics.get('title', '')
    if not topic_title:
        topic_title = "未命名主题"
    
    # 转义XML特殊字符
    topic_title = saxutils.escape(topic_title)
    
    logger.debug(f"处理主题: {topic_title[:30]}{'...' if len(topic_title) > 30 else ''}, 长度: {len(topic_title)}")
    
    # 获取子主题，兼容两种字段格式
    children = []
    if 'children' in topics and topics['children']:
        children = topics['children']
    elif 'topics' in topics and topics['topics']:
        children = topics['topics']
    
    # 设置分支折叠
    folded = 'true' if level > 2 and len(children) > 50 else 'false'
    
    # 添加时间戳和标识符 - XMind需要这些属性
    timestamp = str(int(time.time() * 1000))
    
    # 增加样式支持
    style_id = ""
    if level == 1:
        style_id = ' style-id="centralTopic"'
    elif level == 2:
        style_id = ' style-id="mainTopic"'
    elif level > 5:  # 超深层次使用浮动主题样式
        style_id = ' style-id="floatingTopic"'
    
    # 为超长主题添加文字处理
    if len(topic_title) > 100:
        topic_title = topic_title[:97] + "..."
    
    # 添加主题开始标记 - 确保格式正确    
    chunks.append(f'<topic id="{parent_id}"{style_id} timestamp="{timestamp}" folded="{folded}">')
    chunks.append(f'<title>{topic_title}</title>')
    
    # 处理子主题，如果存在
    if children:
        # XMind的标准结构要求，children标签必须包含topics标签
        chunks.append('<children>')
        chunks.append('<topics type="attached">')  # 这个标签很重要
        
        # 为超大量子主题优化处理
        if len(children) > 1000:
            logger.warning(f"主题 '{topic_title[:30]}...' 有 {len(children)} 个子主题，分批处理")
            # 切片方式处理，避免递归深度过大
            batch_size = 200
            for i in range(0, len(children), batch_size):
                batch = children[i:i+batch_size]
                logger.debug(f"处理批次 {i//batch_size + 1}/{(len(children)-1)//batch_size + 1}, 包含 {len(batch)} 个主题")
                
                for idx, child in enumerate(batch):
                    child_id = f"{parent_id}_{i+idx}"
                    child_xml = generate_topic_xml_optimized(child, child_id, layout_strategy, level + 1)
                    chunks.append(child_xml)
        else:
            for idx, child in enumerate(children):
                child_id = f"{parent_id}_{idx}"
                child_xml = generate_topic_xml_optimized(child, child_id, layout_strategy, level + 1)
                chunks.append(child_xml)
        
        # 关闭topics和children标签
        chunks.append('</topics>')
        chunks.append('</children>')
    
    # 关闭topic标签
    chunks.append('</topic>')
    
    return '\n'.join(chunks)

def generate_relationships(max_relationships=100):
    """
    生成关系XML，为大型思维导图添加一定数量的关系线
    
    Args:
        max_relationships (int): 最大关系数量
        
    Returns:
        str: 生成的关系XML字符串
    """
    if max_relationships <= 0:
        return ""
        
    xml = "<relationships>"
    
    # 创建一些示例关系，实际应用中可能需要根据主题间的逻辑关系来创建
    for i in range(min(30, max_relationships)):
        rel_id = f"rel_{i}"
        source_id = f"root_{i}"
        target_id = f"root_{min(i+5, max_relationships-1)}"
        
        # 添加不同类型的关系线
        rel_type = "arrowedline"
        if i % 3 == 0:
            rel_type = "dashedarrowline"
        elif i % 5 == 0:
            rel_type = "straightline"
            
        xml += f'<relationship end1="{source_id}" end2="{target_id}" id="{rel_id}" timestamp="1615975489000" type="{rel_type}"/>'
    
    xml += "</relationships>"
    return xml

def create_thumbnail_image(structure, output_path, size=(128, 128)):
    """创建标准缩略图"""
    try:
        # 创建一个简单的白色缩略图
        img = Image.new('RGB', size, color='white')
        draw = ImageDraw.Draw(img)
        
        # 尝试获取字体
        try:
            font = ImageFont.truetype("Arial", 12)
        except IOError:
            font = ImageFont.load_default()
        
        # 绘制一个基本的XMind缩略图
        title = structure.get('title', 'Mind Map')
        if len(title) > 15:
            title = title[:12] + '...'
        
        # 绘制缩略图
        draw.rectangle(((10, 50), (118, 78)), fill="#4675EB", outline="#4675EB")
        draw.text((15, 55), title, fill="white", font=font)
        
        # 保存图像 - 确保是PNG格式
        img.save(output_path, format='PNG')
        logger.debug(f"标准缩略图创建成功: {output_path}")
    except Exception as e:
        logger.error(f"创建缩略图出错: {e}")
        # 保存一个最小的PNG图像
        try:
            # 最简单的有效PNG
            minimal_png = (
                b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00'
                b'\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDAT'
                b'\x08\x99c\xf8\xff\xff?\x00\x05\xfe\x02\xfe\xdc\xcc\x59\xe7'
                b'\x00\x00\x00\x00IEND\xaeB`\x82'
            )
            with open(output_path, 'wb') as f:
                f.write(minimal_png)
            logger.debug(f"最小PNG缩略图创建成功: {output_path}")
        except Exception as e2:
            logger.error(f"创建最小PNG也失败: {e2}")

def get_xmind_pro_styles():
    """返回XMind官方格式的样式文件内容"""
    return """<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<xmap-styles xmlns="urn:xmind:xmap:xmlns:style:2.0" xmlns:fo="http://www.w3.org/1999/XSL/Format" version="2.0">
  <automatic-styles>
    <style id="0bjllfq8ghidkddh57pckr1vv1" name="主题" type="theme">
      <theme-properties>
        <default-style id="2cql1lcl37i1d2g9urf5ndkf38"/>
        <line-tapered>none</line-tapered>
        <structure inherit="0r0bfavd1d6aeg2f0ejat0ktml" type="org.xmind.ui.map"/>
      </theme-properties>
    </style>
    <style id="0r0bfavd1d6aeg2f0ejat0ktml" name="Map" type="structure">
      <structure-properties>
        <layout>org.xmind.ui.map.clockwise</layout>
      </structure-properties>
    </style>
    <style id="2cql1lcl37i1d2g9urf5ndkf38" name="Map" type="map">
      <map-properties>
        <multi-line-colors>0,102,204 255,102,0</multi-line-colors>
        <gradient-color>-32896</gradient-color>
        <line-width>1pt</line-width>
        <svg:fill>rgb(238,238,238)</svg:fill>
      </map-properties>
    </style>
    <style id="6afjv8q05a8uhd1drvam3e4nf3" name="Central Topic" type="topic">
      <topic-properties>
        <svg:fill>rgb(0,102,204)</svg:fill>
        <line-class>org.xmind.branchConnection.curve</line-class>
        <line-width>1pt</line-width>
        <shape-class>org.xmind.topicShape.rounded.rect</shape-class>
        <line-color>rgb(0,102,204)</line-color>
        <border-line-width>1pt</border-line-width>
        <border-line-color>rgb(0,102,204)</border-line-color>
        <fo:font-family>Avenir Next</fo:font-family>
        <fo:font-weight>normal</fo:font-weight>
        <fo:font-style>normal</fo:font-style>
        <fo:font-size>17pt</fo:font-size>
        <fo:text-transform>capitalize</fo:text-transform>
        <fo:text-decoration>none</fo:text-decoration>
        <fo:color>rgb(255,255,255)</fo:color>
      </topic-properties>
    </style>
    <style id="1lmtnnrm1d4luhufg5pn0t3jq3" name="Main Topic" type="topic">
      <topic-properties>
        <svg:fill>rgb(245,245,245)</svg:fill>
        <fo:font-family>Avenir Next</fo:font-family>
        <fo:font-weight>normal</fo:font-weight>
        <fo:font-style>normal</fo:font-style>
        <fo:font-size>14pt</fo:font-size>
        <fo:text-transform>none</fo:text-transform>
        <fo:text-decoration>none</fo:text-decoration>
        <fo:color>rgb(51,51,51)</fo:color>
        <border-line-width>1pt</border-line-width>
        <border-line-color>rgb(0,102,204)</border-line-color>
        <line-class>org.xmind.branchConnection.curve</line-class>
        <line-width>1pt</line-width>
        <line-color>rgb(0,102,204)</line-color>
        <shape-class>org.xmind.topicShape.roundedRect</shape-class>
      </topic-properties>
    </style>
    <style id="44j09rlsqk2h0igtrme3nvlqbf" name="Subtopic" type="topic">
      <topic-properties>
        <svg:fill>rgb(245,245,245)</svg:fill>
        <fo:font-family>Avenir Next</fo:font-family>
        <fo:font-weight>normal</fo:font-weight>
        <fo:font-style>normal</fo:font-style>
        <fo:font-size>12pt</fo:font-size>
        <fo:text-transform>none</fo:text-transform>
        <fo:text-decoration>none</fo:text-decoration>
        <fo:color>rgb(51,51,51)</fo:color>
        <border-line-width>1pt</border-line-width>
        <border-line-color>rgb(0,102,204)</border-line-color>
        <line-class>org.xmind.branchConnection.curve</line-class>
        <line-width>1pt</line-width>
        <line-color>rgb(0,102,204)</line-color>
        <shape-class>org.xmind.topicShape.roundedRect</shape-class>
      </topic-properties>
    </style>
    <style id="3hdnt83tpfp0bg6sdn7a0ujvmu" name="Floating Topic" type="topic">
      <topic-properties>
        <svg:fill>rgb(245,245,245)</svg:fill>
        <fo:font-family>Avenir Next</fo:font-family>
        <fo:font-weight>normal</fo:font-weight>
        <fo:font-style>normal</fo:font-style>
        <fo:font-size>14pt</fo:font-size>
        <fo:text-transform>none</fo:text-transform>
        <fo:text-decoration>none</fo:text-decoration>
        <fo:color>rgb(51,51,51)</fo:color>
        <border-line-width>1pt</border-line-width>
        <border-line-color>rgb(0,102,204)</border-line-color>
        <line-class>org.xmind.branchConnection.curve</line-class>
        <line-width>1pt</line-width>
        <line-color>rgb(0,102,204)</line-color>
        <shape-class>org.xmind.topicShape.underline</shape-class>
      </topic-properties>
    </style>
  </automatic-styles>
  <master-styles>
    <style id="0bjllfq8ghidkddh57pckr1vv1" name="主题" type="theme">
      <style-rules>
        <rule branch="central" style-id="6afjv8q05a8uhd1drvam3e4nf3"/>
        <rule branch="main" style-id="1lmtnnrm1d4luhufg5pn0t3jq3"/>
        <rule branch="sub" style-id="44j09rlsqk2h0igtrme3nvlqbf"/>
        <rule branch="floating" style-id="3hdnt83tpfp0bg6sdn7a0ujvmu"/>
      </style-rules>
    </style>
  </master-styles>
</xmap-styles>"""

def create_fallback_xmind(structure, output_path):
    """
    Create a fallback XMind file in case of errors.
    
    Args:
        structure (dict): The structure to include
        output_path (str): The output path
        
    Returns:
        str: The output path
    """
    try:
        import xmind
        # Create a new workbook
        workbook = xmind.load(output_path)
        
        # Get the first sheet
        sheet = workbook.getPrimarySheet()
        
        # Set the root topic
        root_topic = sheet.getRootTopic()
        root_title = structure.get("title", "思维导图")
        root_topic.setTitle(root_title)
        
        # 获取子主题，兼容两种字段格式
        subtopics = []
        if 'children' in structure and structure['children']:
            subtopics = structure['children']
        elif 'topics' in structure and structure['topics']:
            subtopics = structure['topics']
        
        # Recursively add topics
        if subtopics:
            add_topics(root_topic, subtopics)
        
        # Save the workbook
        xmind.save(workbook)
        
        return output_path
    except Exception as e:
        logger.error(f"Error creating fallback XMind file: {e}")
        # If all else fails, create a very basic ZIP file with XMind structure
        return create_basic_xml_xmind(structure, output_path)

def add_topics(parent_topic, topics):
    """
    Recursively add topics to a parent topic.
    
    Args:
        parent_topic: The parent XMind topic.
        topics (list): List of topic dictionaries with 'title' and 'children' or 'topics' keys.
    """
    for topic_data in topics:
        # Create a new topic
        topic = parent_topic.addSubTopic()
        topic.setTitle(topic_data["title"])
        
        # 获取子主题，兼容两种字段格式
        subtopics = []
        if 'children' in topic_data and topic_data['children']:
            subtopics = topic_data['children']
        elif 'topics' in topic_data and topic_data['topics']:
            subtopics = topic_data['topics']
        
        # Add subtopics recursively
        if subtopics:
            add_topics(topic, subtopics)

def create_basic_xml_xmind(structure, output_path):
    """
    Create a very basic XMind XML-based file for last-resort fallback.
    
    Args:
        structure (dict): The structure to include
        output_path (str): The output path
        
    Returns:
        str: The output path
    """
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Create basic content.xml - 使用极度简化版本
        content_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<xmap-content xmlns="urn:xmind:xmap:xmlns:content:2.0" version="2.0">
  <sheet id="sheet1">
    <topic id="root" structure-class="org.xmind.ui.map.unbalanced">
      <title>{structure["title"]}</title>
    </topic>
    <title>Sheet 1</title>
  </sheet>
</xmap-content>"""
        
        with open(os.path.join(temp_dir, 'content.xml'), 'w', encoding='utf-8') as f:
            f.write(content_xml)
        
        # Create minimal meta.xml
        meta_xml = """<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<meta xmlns="urn:xmind:xmap:xmlns:meta:2.0" version="2.0">
  <Author><Name>Text2Mind</Name></Author>
</meta>"""
        
        with open(os.path.join(temp_dir, 'meta.xml'), 'w', encoding='utf-8') as f:
            f.write(meta_xml)
        
        # Create manifest.xml
        manifest_xml = """<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<manifest xmlns="urn:xmind:xmap:xmlns:manifest:1.0">
  <file-entry full-path="content.xml" media-type="text/xml"/>
  <file-entry full-path="meta.xml" media-type="text/xml"/>
  <file-entry full-path="META-INF/" media-type=""/>
  <file-entry full-path="META-INF/manifest.xml" media-type="text/xml"/>
</manifest>"""
        
        os.makedirs(os.path.join(temp_dir, 'META-INF'), exist_ok=True)
        with open(os.path.join(temp_dir, 'META-INF', 'manifest.xml'), 'w', encoding='utf-8') as f:
            f.write(manifest_xml)
        
        # Create the ZIP with maximum compression
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as zipf:
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(file_path, temp_dir)
                    zipf.write(file_path, rel_path)
        
        return output_path
    except Exception as e:
        print(f"Error creating basic XMind ZIP: {e}")
        return output_path
    finally:
        shutil.rmtree(temp_dir)

def export_xmind_to_png(xmind_path, png_path=None):
    """
    Export an XMind file to PNG image.
    
    Args:
        xmind_path (str): Path to the XMind file.
        png_path (str, optional): Path where the PNG will be saved. If None, uses the same name as XMind.
        
    Returns:
        str: The path to the created PNG file.
    """
    if png_path is None:
        png_path = os.path.splitext(xmind_path)[0] + ".png"
    
    try:
        # Try using xmindparser for export
        import xmindparser
        xmindparser.config['showTopicId'] = False
        xmindparser.config['hideEmptyValue'] = True
    except ImportError:
        pass
    
    # For this example, we'll create a simple mind map visualization with PIL
    # since the actual XMind export can be complex
    
    # Create a simple mind map visualization
    structure = create_simple_mind_map_structure(xmind_path)
    
    # Draw the mind map
    img = draw_mind_map(structure)
    
    # Save the image
    img.save(png_path)
    
    return png_path

def create_simple_mind_map_structure(xmind_path):
    """
    Create a simple structure for visualization.
    In a real app, this would parse the XMind file.
    
    For simplicity, we'll just create a structure based on the
    hierarchy we created earlier.
    """
    try:
        # Try to read the actual xmind file
        import xmindparser
        content = xmindparser.xmind_to_dict(xmind_path)
        if content and isinstance(content, list) and len(content) > 0:
            return content[0].get("topic", {})
        
        # If xmindparser doesn't work, create a simple structure
        return {"title": "Sample Mind Map", "topics": []}
    except:
        # Fallback to a simple structure
        return {"title": "Sample Mind Map", "topics": []}

def draw_mind_map(structure):
    """
    Draw a simple mind map visualization.
    
    Args:
        structure (dict): The structure to visualize.
        
    Returns:
        PIL.Image: The generated image.
    """
    # Create a white canvas - 增加画布宽度
    img = Image.new('RGB', (2000, 1200), color='white')
    draw = ImageDraw.Draw(img)
    
    # Try to get a font
    try:
        font_large = ImageFont.truetype("Arial", 20)
        font_medium = ImageFont.truetype("Arial", 16)
        font_small = ImageFont.truetype("Arial", 12)
    except IOError:
        # Fallback to default font
        font_large = ImageFont.load_default()
        font_medium = font_large
        font_small = font_large
    
    # Draw the root node - 将根节点放在左侧
    root_title = structure.get("title", "Mind Map")
    draw.rectangle(((100, 580), (250, 620)), fill="#4475E3", outline="black")
    draw.text((110, 590), root_title, fill="white", font=font_large)
    
    # 兼容两种字段格式获取主题
    topics = []
    if 'children' in structure:
        topics = structure.get('children', [])
    elif 'topics' in structure:
        topics = structure.get('topics', [])
    
    if topics:
        y_spacing = 800 // (len(topics) + 1)
        for i, topic in enumerate(topics):
            title = topic.get("title", f"Topic {i+1}")
            y = 200 + (i+1) * y_spacing
            
            # Draw the topic box
            draw.rectangle(((300, y), (500, y+30)), fill="lightyellow", outline="black")
            draw.text((310, y+5), title, fill="black", font=font_medium)
            
            # Draw line to root
            draw.line(((300, y+15), (250, 600)), fill="black", width=2)
            
            # 兼容两种字段格式获取子主题
            subtopics = []
            if 'children' in topic:
                subtopics = topic.get('children', [])
            elif 'topics' in topic:
                subtopics = topic.get('topics', [])
            
            if subtopics:
                sub_y_spacing = y_spacing // (len(subtopics) + 1)
                for j, subtopic in enumerate(subtopics):
                    sub_title = subtopic.get("title", f"Subtopic {j+1}")
                    sub_y = y - (y_spacing // 3) + (j+1) * sub_y_spacing
                    
                    # Draw the subtopic box
                    draw.rectangle(((550, sub_y), (750, sub_y+25)), fill="lightgreen", outline="black")
                    draw.text((560, sub_y+2), sub_title, fill="black", font=font_small)
                    
                    # Draw line to parent topic
                    draw.line(((550, sub_y+12), (500, y+15)), fill="black", width=1)
                    
                    # 兼容两种字段格式获取子子主题
                    sub_subtopics = []
                    if 'children' in subtopic:
                        sub_subtopics = subtopic.get('children', [])
                    elif 'topics' in subtopic:
                        sub_subtopics = subtopic.get('topics', [])
                    
                    if sub_subtopics:
                        sub_sub_y_spacing = sub_y_spacing // (len(sub_subtopics) + 1)
                        for k, sub_subtopic in enumerate(sub_subtopics):
                            sub_sub_title = sub_subtopic.get("title", f"Sub-subtopic {k+1}")
                            sub_sub_y = sub_y - (sub_y_spacing // 3) + (k+1) * sub_sub_y_spacing
                            
                            # Draw the sub-subtopic box
                            draw.rectangle(((800, sub_sub_y), (1000, sub_sub_y+20)), fill="lightpink", outline="black")
                            draw.text((810, sub_sub_y+2), sub_sub_title, fill="black", font=font_small)
                            
                            # Draw line to parent subtopic
                            draw.line(((800, sub_sub_y+10), (750, sub_y+12)), fill="black", width=1)
    
    return img

def create_content_xml(temp_dir, parsed_data, layout_strategy):
    """创建content.xml文件"""
    content_path = os.path.join(temp_dir, 'content.xml')
    
    # 记录开始时间，用于性能监控
    start_time = time.time()
    
    # 根据节点数量选择生成方法
    node_count = count_nodes(parsed_data)
    logger.info(f"创建content.xml，共有 {node_count} 个节点, 布局策略: {layout_strategy}")
    
    # 设置适当的缓冲区大小，根据节点数量扩大
    buffer_size = max(10 * 1024 * 1024, node_count * 500)  # 至少10MB
    
    # 生成时间戳和ID
    timestamp = str(int(time.time() * 1000))
    sheet_id = f"sheet_{timestamp[:8]}"
    
    with open(content_path, 'w', encoding='utf-8', buffering=buffer_size) as f:
        # 写入XML头部
        f.write('<?xml version="1.0" encoding="UTF-8" standalone="no"?>')
        f.write('<xmap-content xmlns="urn:xmind:xmap:xmlns:content:2.0" xmlns:fo="http://www.w3.org/1999/XSL/Format" xmlns:svg="http://www.w3.org/2000/svg" xmlns:xhtml="http://www.w3.org/1999/xhtml" xmlns:xlink="http://www.w3.org/1999/xlink" modified-by="XMind" timestamp="' + timestamp + '" version="2.0">')
        
        # 写入sheets开始标签
        f.write(f'<sheet id="{sheet_id}" timestamp="{timestamp}" theme="0bjllfq8ghidkddh57pckr1vv1">')
        f.write(f'<topic id="root" timestamp="{timestamp}" structure-class="{layout_strategy}">')
        
        # 处理根主题
        root_title = parsed_data.get('title', '思维导图')
        root_title = saxutils.escape(root_title)
        f.write(f'<title>{root_title}</title>')
        f.write('<position x="121" y="133"/>')
        
        # 兼容两种字段格式获取子主题
        children = []
        if 'children' in parsed_data and parsed_data['children']:
            children = parsed_data['children']
        elif 'topics' in parsed_data and parsed_data['topics']:
            children = parsed_data['topics']
        
        # 处理子主题，使用优化的方法
        if children:
            f.write('<children>')
            f.write('<topics type="attached">')  # 这是XMind的规范格式
            
            # 使用分批处理方式
            batch_size = 200
            
            # 检查子主题数量
            if len(children) > 1000:
                logger.warning(f"根主题有 {len(children)} 个子主题，分批处理")
                
                for i in range(0, len(children), batch_size):
                    batch = children[i:i+batch_size]
                    logger.debug(f"处理批次 {i//batch_size + 1}/{(len(children)-1)//batch_size + 1}, "
                                f"包含 {len(batch)} 个主题")
                    
                    for idx, child in enumerate(batch):
                        child_id = f"root_{i+idx}"
                        # 直接写入，避免过多字符串连接
                        child_xml = generate_topic_xml_optimized(child, child_id, layout_strategy)
                        f.write(child_xml)
                        # 强制刷新到文件
                        if (i+idx) % 100 == 0:
                            f.flush()
            else:
                for idx, child in enumerate(children):
                    child_id = f"root_{idx}"
                    child_xml = generate_topic_xml_optimized(child, child_id, layout_strategy)
                    f.write(child_xml)
            
            f.write('</topics>')
            f.write('</children>')
        
        # 写入sheets结束标签
        f.write('</topic>')
        f.write('<title>Sheet 1</title>')  # 添加sheet标题
        
        # 添加关系，如果节点很多，则只处理部分
        max_relationships = min(30, node_count // 100)
        f.write(generate_relationships(max_relationships))
        
        f.write('</sheet>')
        f.write('</xmap-content>')
    
    # 记录完成时间
    elapsed = time.time() - start_time
    logger.info(f"content.xml创建完成，用时 {elapsed:.2f} 秒")
    
    # 检查文件大小
    file_size = os.path.getsize(content_path)
    logger.info(f"content.xml文件大小: {file_size/1024/1024:.2f} MB")
    
    return content_path 