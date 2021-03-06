import copy
import lxml.cssselect
import lxml.etree
import lxml.html.clean
import itertools

bad_tags = [
    'head',
    'header',
    'footer',
    'nav',
    #'form',
    'svg',
    'figure',
    'aside',
    ]
xpath_rm_nodes = '|'.join('(descendant-or-self::'+tag+')' for tag in bad_tags)
cxpath_rm_nodes = lxml.etree.XPath(xpath_rm_nodes)

# FIXME:
# Should we really remove everything within forms?
# Some websites wrap the entire page within a form.
# file:///home/user/proj/metahtml/tests/.cache/https___education.ky.gov_443_districts_SHS_Pages_2019-Novel-Coronavirus.aspx992feb89/2020-07-17
# file:///home/user/proj/metahtml/tests/.cache/https___elperuano.pe_noticia-corea-del-norte-modernizo-sus-misiles-79420.aspxc3178290/2020-05-30
# file:///home/user/proj/metahtml/tests/.cache/https___www.passeportsante.net_fr_Maux_Problemes_Fiche.aspx_doc=maladie-charbon01924e11/2020-07-06

cxpath_p = lxml.etree.XPath('descendant-or-self::p')
cxpath_main = lxml.etree.XPath('descendant-or-self::main')
cxpath_section = lxml.etree.XPath('descendant-or-self::section')
cxpath_article = lxml.etree.XPath('descendant-or-self::article')
cxpath_div = lxml.etree.XPath('descendant-or-self::div')
cxpath_script_style_comments = lxml.etree.XPath('(descendant-or-self::script)|(descendant-or-self::style)|(descendant-or-self::comment())')

# FIXME:
# currently, this removes all <div> tags;
# for most webpages, content is contained within a <p> tag within a <div> tag,
# but if not <p> is present, then the content will be deleted
# FIXME: uses <br> to separate paragraphs
# some webpages don't store content within <p> tags;
# file:///home/user/proj/metahtml/tests/.cache/https___abc13.com_politics_president-trump-meets-with-kim-jong-un-at-summit_5159138_1f916455/2020-06-23
# file:///home/user/proj/metahtml/tests/.cache/https___abc7chicago.com_news_kim-jong-un-isnt-the-first-dictator-to-go-missing_346174_274f3fef/2020-06-23
# file:///home/user/proj/metahtml/tests/.cache/https___abc7news.com_donald-trump-meeting-with-kim-jong-un-and-summit_5122815_fc051a09/2020-06-23
# file:///home/user/proj/metahtml/tests/.cache/https___dzuturum.blogspot.com_2015_07_chinese-fan-has-plastic-surgery-to-look.html4295804b/2020-06-24
# file:///home/user/proj/metahtml/tests/.cache/https___economictimes.indiatimes.com_magazines_panache_when-kim-jong-uns-influential-aunt-turned-to-dr-d-for-advice_articleshow_74168309.cms3aac81b8/2020-06-24
# file:///home/user/proj/metahtml/tests/.cache/https___en.antaranews.com_news_140151_thermal-scanner-at-bali-airport-to-screen-wuhan-corona-viruse3d53729/2020-07-17
# FIXME: contained within <div>
# file:///home/user/proj/metahtml/tests/.cache/https___www.spicee.com_fr_program_irak-les-mordeuses-de-daesh-1163ec2036e8/2020-07-05
# file:///home/user/proj/metahtml/tests/.cache/https___angelfalques.blogspot.com_2020_03_kim-jong-un-responds-to-coronavirus.html1cb7abc9/2020-06-23
# file:///home/user/proj/metahtml/tests/.cache/https___economictimes.indiatimes.com_news_international_world-news_kim-jong-un-here-are-some-interesting-facts-about-north-koreas-absolute-master_articleshow_64429914.cmsc1439ac9/2020-06-24
# file:///home/user/proj/metahtml/tests/.cache/https___edition.cnn.com_2019_12_04_asia_north-korea-christmas-gift-kim-jong-un-intl-hnk_index.html19b38b76/2020-05-30
#
# FIXME: still broken
# file:///home/user/proj/metahtml/tests/.cache/https___www.tishineh.com_touritem_1258_Sassani-fire-Temple-of-Natanzaf31b3d8/2020-07-01
# file:///home/user/proj/metahtml/tests/.cache/https___www.tishineh.com_touritem_1258-134_%D8%A2%D8%AA%D8%B4%DA%A9%D8%AF%D9%87-%D8%B3%D8%A7%D8%B3%D8%A7%D9%86%DB%8C-%D9%86%D8%B7%D9%86%D8%B2e13d79d0/2020-07-01
# file:///home/user/proj/metahtml/tests/.cache/https___www.timetoast.com_timelines_historique-bioterrorismea36cc622/2020-07-14
# file:///home/user/proj/metahtml/tests/.cache/https___www.thereligionofpeace.com_pages_quran_violence.aspx82179f7a/2020-07-05
# file:///home/user/proj/metahtml/tests/.cache/https___www.statista.com_statistics_294305_iran-unemployment-rate_07d66fdf/2020-07-03

tags_section = ['address','article','aside','figcaption','figure','main','section']
tags_inline = ['a','span']
tags_list = ['ul', 'ol', 'li', 'dl', 'dt', 'dd']
tags_block = ['p','blockquote']
tags_header = ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']
tags_code = ['tt', 'pre', 'code']
tags_table = ['table','tr','td','th','colgroup','col','tbody','thead','tfoot','caption','tbody']
article_cleaner = lxml.html.clean.Cleaner()
article_cleaner.javascript = True
article_cleaner.style = True
article_cleaner.remove_unknown_tags = False
article_cleaner.allow_tags = (
    tags_section + 
    tags_inline +
    tags_block + 
    tags_header + 
    tags_code +
    tags_list +
    tags_table +
    ['br'] # FIXME: replace <br> with <p>?
    )

def simple_extractor(parser):
    doc = parser.doc
    url_parsed = parser.url_parsed
    #url_parsed = urlparse(url)
    confidence = 'lo'

    # delete nodes that never contain content
    for node in cxpath_script_style_comments(doc):
        remove_node_keep_tail(node)

    # the <main> tag indicates the main body of html5 text;
    # if present, restrict our search just to this tag
    mains = list(cxpath_main(doc))
    if len(mains)==1:
        doc = mains[0]
        confidence = 'hi'

    '''
    FIXME:
    should we include this?
    # the <section> tag indicates the section body of html5 text;
    # if present, restrict our search just to this tag
    sections = list(cxpath_section(doc))
    if len(sections)==1:
        doc = sections[0]
        confidence = 'hi'
    '''

    # the <article> tag indicates that an article is present;
    # unlike the main tag, there is commonly more than 1 <article> tag per page;
    # these multiple <article> tags occur on category pages that link to many articles,
    # and in "related pages" sections;
    # in both of these cases, only small snippets of the actual article are in the html;;
    # in the former case, we want to extract nothing;
    # in the latter case, we want to extract only the large main article;
    # we achieve both goals by using the article tag only if its length is greater than twice 
    # the average of all other article tags
    # FIXME:
    # the twice heuristic hasn't been tested and other numbers might reduce false positives/negatives
    # FIXME:
    # these checks should be in the article_type.py file as well
    articles = list(cxpath_article(doc))
    if len(articles)==1:
        # some webpages use the <article> tag only around related articles links,
        # and not around the main article;
        # counting for <p> tags ensures we don't miss the main article on these pages
        article = articles[0]
        article_text = text_content(article)
        if len(cxpath_p(article))>1 or len(article_text)>1000:
            doc = articles[0]
            confidence = 'hi'
    elif len(articles)>1:
        articles_lens = []
        for article in articles:
            articles_lens.append(len(text_content(article)))
        largest = max(articles_lens)
        mean_minus_largest = (sum(articles_lens) - largest) / (len(articles_lens) - 1)
        if largest > mean_minus_largest*2:
            largest_index = articles_lens.index(largest)
            doc = articles[largest_index]
            confidence = 'hi'

    # remove nodes that are semantically unrelated to the article's content;
    # FIXME:
    # should we be storing the figure/aside tags separately for later processing?
    for node in list(cxpath_rm_nodes(doc)):
        node.getparent().remove(node)

    # change <div> tags to <p> tags if they don't contain block elements;
    # many webpages do not use <p> tags at all and only use <div> tags,
    # and this conversion lets us capture the text on these pages
    # FIXME:
    # should we only do this if there are no/few <p> tags?
    for div in doc.iterdescendants('div'):
    #for div in list(cxpath_div(doc)):
        # compute has_block
        has_block = False
        for descendant in div.iterdescendants():
            if descendant.tag in tags_section + tags_list + tags_block + ['div']:
                next_br = descendant.getnext() is not None and descendant.getnext().tag == 'br'
                prev_br = descendant.getprevious() is not None and descendant.getprevious().tag == 'br'
                if not (next_br or prev_br):
                    has_block = True

        # compute div_text
        div_text = ''
        div_text_threshold = 20
        if div.text is not None:
            div_text += div.text.strip()
        for child in div.getchildren():
            if child.tag not in ['div']+tags_block+tags_section+tags_list:
                div_text += ' ' + text_content(child)
            else:
                child_tail = ''
                if child.tail is not None:
                    child_tail = child.tail.strip()
                div_text += child_tail
            if len(div_text)>div_text_threshold:
                break

        # process div 
        if len(div_text)>div_text_threshold or not has_block:
            div.tag = 'p'
            # replace <br> tags with a series of <p> tags
            # 
            #   <div>a<br>b<a>c</a>d<br>e</div>
            #
            # becomes
            #
            #   <p>a</p>
            #   <p>b<a>c</a>d</p>
            #   <p>e</p>
            children = list(div.getchildren())
            for child in children:
                div.remove(child)
            for child in children:
                if child.tag in ['br']: #,'div']+tags_block+tags_section+tags_list:
                    new_div = lxml.etree.Element('p')
                    new_div.set('created_from_div_br','true')
                    new_div.text = child.tail
                    div.addnext(new_div)
                    div = new_div
                else:
                    div.append(child)

    # clean the html to remove all unwanted tags
    # FIXME: breaks some webpages for unknown reason
    # file:///home/user/proj/metahtml/tests/.cache/https___www.public.fr_News_Lionel-Messi-Menace-par-Daesh-1444943dd2edccb/2020-07-05.diff.html
    # FIXME: table gets converted into <p>
    # file:///home/user/proj/metahtml/tests/.cache/https___www.uppersia.com_Iran-hotels_natanz-hotels.htmle84d1498/2020-07-01.diff.html
    doc = article_cleaner.clean_html(doc)

    # recursively remove empty nodes
    def go(doc):
        children = list(doc.getchildren())
        for child in children:
            child = go(child)
        has_text = doc.text is not None and doc.text.strip() != ''
        if not has_text and len(doc)==0:
            remove_node_keep_tail(doc)
            #doc.getparent().remove(doc)
        return doc
    doc = go(doc)

    # lists that don't come after at least 2 <p> tags are probably header info
    # FIXME: removes too much
    # file:///home/user/proj/metahtml/tests/.cache/https___www.businessinsider.com_trump-deploys-hospital-ship-mercy-to-los-angeles-2020-344984c01/2020-06-16.diff.html
    # file:///home/user/proj/metahtml/tests/.cache/https___www.sunsigns.org_famousbirthdays_profile_ayatollah-ruhollah-khomeini_b65082cc/2020-07-03.diff.html
    allow_lists = False
    nodes_to_remove = []
    for node in doc.iter():
        if not allow_lists and node.tag in tags_list:
            nodes_to_remove.append(node)
        if node.tag=='h1':
            allow_lists = True
        if node.tag=='p': # and node.getprevious() is not None and node.getprevious().tag=='p':
            text = text_content(node)
            if len(text)<20 or '©' in text or '.' not in text:
                if not allow_lists:
                    nodes_to_remove.append(node)
            else:
                if not any(block in [ node.tag for node in node.iterancestors() ] for block in tags_list):
                    allow_lists = True
    for node in nodes_to_remove:
        if node.getparent() is not None:
            node.getparent().remove(node)
    
    # lists/headers at the end of the page without following <p> tags are probably footer info
    # FIXME: removes too little
    # file:///home/user/proj/metahtml/tests/.cache/https___arabic.sputniknews.com_world_202004081045105540-%25D8%25A7%25D9%2584%25D8%25B5%25D9%258A%25D9%2586-%25D8%25AA%25D8%25B3%25D8%25AC%25D9%2584-62-%25D8%25A5%25D8%25B5%25D8%25A7%25D8%25A8%25D8%25A9-%25D8%25AC%25D8%25AF%25D9%258A%25D8%25AF%25D8%25A9-%25D8%25A8%25D9%2581%25D9%258A%255c44ca74/
    # file:///home/user/proj/metahtml/tests/.cache/http___21stcenturywire.com_2018_05_07_gareth-porter-did-john-bolton-leak-intelligence-to-sabotage-a-trump-kim-deal_02bc34fa/2020-06-02.diff.html
    # file:///home/user/proj/metahtml/tests/.cache/https___allthingsnuclear.org_dwright_north-koreas-latest-missile-test7b6fb667/2020-05-30.diff.html
    # file:///home/user/proj/metahtml/tests/.cache/https___www.saphirnews.com_Que-dit-la-presse-arabe-sur-Daesh_a20186.html3c616d4a/2020-07-14.metahtml.html
    # file:///home/user/proj/metahtml/tests/.cache/https___www.tomsguide.fr_impact-mobilisation-internationale-contre-le-cyberterrorisme_1694d90c/2020-07-05.diff.html
    # file:///home/user/proj/metahtml/tests/.cache/https___www.semana.com_deportes_articulo_en-grave-peligro-hermetismo-sobre-estado-de-salud-de-kim-jong-un-tras-cirugia_664851c8fcfae6/2020-05-31.metahtml.html
    # FIXME: removes too much
    # file:///home/user/proj/metahtml/tests/.cache/https___www.thefamouspeople.com_profiles_ayatollah-khomeini-12.phpb8cbce93/2020-07-07.diff.html
    # file:///home/user/proj/metahtml/tests/.cache/https___www.sunsigns.org_famousbirthdays_profile_ayatollah-ruhollah-khomeini_b65082cc/2020-07-03.diff.html
    # file:///home/user/proj/metahtml/tests/.cache/https___english.khabarhub.com_2019_11_20114_24c28975/
    # file:///home/user/proj/metahtml/tests/.cache/https___www.police-nationale.interieur.gouv.fr_Organisation_Entites-rattachees-directement-au-DGPN_UCLATd58cd76b/2020-07-14.diff.html
    # file:///home/user/proj/metahtml/tests/.cache/https___www.thefamouspeople.com_profiles_ayatollah-khomeini-12.phpb8cbce93/2020-07-07
    # (the html is broken, no </li> tags) file:///home/user/proj/metahtml/tests/.cache/https___www.scientificamerican.com_article_how-does-chlorine-added-t_cdc79060/2020-06-12
    # file:///home/user/proj/metahtml/tests/.cache/https___www.semana.com_deportes_articulo_en-grave-peligro-hermetismo-sobre-estado-de-salud-de-kim-jong-un-tras-cirugia_664851c8fcfae6/2020-05-31.metahtml.html
    allow_lists = False
    nodes_to_remove = []
    for node in reversed(list(doc.iter())):
        if not allow_lists and node.tag in tags_list + tags_header:
            nodes_to_remove.append(node)
        if node.tag=='p':
            text = text_content(node)
            if len(text)<20 or '©' in text or '.' not in text:
                if not allow_lists:
                    nodes_to_remove.append(node)
            else:
                if not any(block in [ node.tag for node in node.iterancestors() ] for block in tags_list):
                    allow_lists = True
    for node in nodes_to_remove:
        if node.getparent() is not None:
            node.getparent().remove(node)

    # remove content not contained within a <p> tag
    nodes_to_remove = []
    for node in doc.iter():
        if node.tag in tags_section + ['div']:
            node.text = None
            node.tail = None
        if node.tag in tags_inline:
            if not any(block in [ node.tag for node in itertools.chain(node.iterancestors(),node.iterdescendants()) ] for block in tags_block+tags_list):
                nodes_to_remove.append(node)

        if node.tail:
            if not any(block in [ node.tag for node in node.iterancestors() ] for block in tags_block+tags_list):
                node.tail = None
        # FIXME:
        # should we remove highlink density tags?
        #if node.tag=='p' and is_highlink_density(node):
            #nodes_to_remove.append(node)
    for node in nodes_to_remove:
        if node.getparent() is not None:
            node.getparent().remove(node)
    
    # convert the parsed lxml document back into html
    html = lxml.etree.tostring(doc,method='html').decode('utf-8')

    return {
        'value' : {
            'text' : '',
            'html' : html,
            },
        'confidence' : confidence,
        'pattern' : 'simple_extractor',
        }

################################################################################

# FIXME: remove all calls to this function?
def text_content(node):
    try:
        return node.text_content()
    except ValueError:
        return ''
    txts = [i for i in node.itertext()]
    return innerTrim(' '.join(txts).strip())

import re
TABSSPACE = re.compile(r'[\s\t]+')
def innerTrim(value):
    if isinstance(value, str):
        # remove tab and white space
        value = re.sub(TABSSPACE, ' ', value)
        value = ''.join(value.splitlines())
        return value.strip()
    return ''

def remove_node_keep_tail(node):
    '''
    The simplest way to remove a node from the lxml parse tree is to directly remove it from the parent with the code:

    > node.getparent().remove(node)

    This can have unexpected behavior when tags have tail text,
    as the tail text will also be removed.
    This function removes the html tag without removing the tail text.

    For details on tail text, see: https://docs.python.org/3/library/xml.etree.elementtree.html#xml.etree.ElementTree.Element.tail
    '''
    parent = node.getparent()
    if parent is not None:
        if node.tail:
            prev = node.getprevious()
            if prev is None:
                if not parent.text:
                    parent.text = ''
                parent.text += ' ' + node.tail
            else:
                if not prev.tail:
                    prev.tail = ''
                prev.tail += ' ' + node.tail
        node.clear()
        parent.remove(node)
