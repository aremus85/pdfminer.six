#!/usr/bin/env python3
"""A command line tool for extracting text and images from PDF and
output it to plain text, html, xml or tags."""
import argparse
import logging
import sys
import os

sys.path.append(os.path.abspath(os.path.dirname(os.path.realpath(__file__)) + "/.."))
import pdfminer.high_level
import pdfminer.layout

logging.basicConfig()

OUTPUT_TYPES = ((".htm", "html"),
                (".html", "html"),
                (".xml", "xml"),
                (".tag", "tag"))


def float_or_disabled(x):
    if x.lower().strip() == "disabled":
        return x
    try:
        x = float(x)
    except ValueError:
        raise argparse.ArgumentTypeError("invalid float value: {}".format(x))


def extract_text(files=[], outfile='-',
                 no_laparams=False, all_texts=None, detect_vertical=None,
                 word_margin=None, char_margin=None, line_margin=None,
                 boxes_flow=None, output_type='text', codec='utf-8',
                 strip_control=False, maxpages=0, page_numbers=None,
                 password="", scale=1.0, rotation=0, layoutmode='normal',
                 output_dir=None, debug=False, disable_caching=False,
                 **kwargs):
    if not files:
        raise ValueError("Must provide files to work upon!")

    # If any LAParams group arguments were passed,
    # create an LAParams object and
    # populate with given args. Otherwise, set it to None.
    if not no_laparams:
        laparams = pdfminer.layout.LAParams()
        for param in ("all_texts", "detect_vertical", "word_margin",
                      "char_margin", "line_margin", "boxes_flow"):
            paramv = locals().get(param, None)
            if paramv is not None:
                setattr(laparams, param, paramv)
    else:
        laparams = None

    if output_type == "text" and outfile != "-":
        for override, alttype in OUTPUT_TYPES:
            if outfile.endswith(override):
                output_type = alttype

    if outfile == "-":
        outfp = sys.stdout
        if outfp.encoding is not None:
            codec = 'utf-8'
    else:
        outfp = open(outfile, "wb")

    info = None
    for fname in files:
        with open(fname, "rb") as fp:
            res = pdfminer.high_level.extract_text_to_fp(fp, **locals())
            if not info:
                info = res
    return (outfp, res)


def maketheparser():
    parser = argparse.ArgumentParser(description=__doc__, add_help=True)
    parser.add_argument(
        "files", type=str, default=None, nargs="+",
        help="One or more paths to PDF files.")

    parser.add_argument(
        "--version", "-v", action="version",
        version="pdfminer.six v{}".format(pdfminer.__version__))
    parser.add_argument(
        "--debug", "-d", default=False, action="store_true",
        help="Use debug logging level.")
    parser.add_argument(
        "--disable-caching", "-C", default=False, action="store_true",
        help="If caching or resources, such as fonts, should be disabled.")

    parse_params = parser.add_argument_group(
        'Parser', description='Used during PDF parsing')
    parse_params.add_argument(
        "--page-numbers", type=int, default=None, nargs="+",
        help="A space-seperated list of page numbers to parse.")
    parse_params.add_argument(
        "--pagenos", "-p", type=str,
        help="A comma-separated list of page numbers to parse. "
             "Included for legacy applications, use --page-numbers "
             "for more idiomatic argument entry.")
    parse_params.add_argument(
        "--maxpages", "-m", type=int, default=0,
        help="The maximum number of pages to parse.")
    parse_params.add_argument(
        "--password", "-P", type=str, default="",
        help="The password to use for decrypting PDF file.")
    parse_params.add_argument(
        "--rotation", "-R", default=0, type=int,
        help="The number of degrees to rotate the PDF "
             "before other types of processing.")

    la_params = parser.add_argument_group(
        'Layout analysis', description='Used during layout analysis.')
    la_params.add_argument(
        "--no-laparams", "-n", default=False, action="store_true",
        help="If layout analysis parameters should be ignored.")
    la_params.add_argument(
        "--detect-vertical", "-V", default=False, action="store_true",
        help="If vertical text should be considered during layout analysis")
    la_params.add_argument(
        "--char-margin", "-M", type=float, default=2.0,
        help="If two characters are closer together than this margin they "
             "are considered to be part of the same line. The margin is "
             "specified relative to the width of the character.")
    la_params.add_argument(
        "--word-margin", "-W", type=float, default=0.1,
        help="If two characters on the same line are further apart than this "
             "margin then they are considered to be two separate words, and "
             "an intermediate space will be added for readability. The margin "
             "is specified relative to the width of the character.")
    la_params.add_argument(
        "--line-margin", "-L", type=float, default=0.5,
        help="If two lines are are close together they are considered to "
             "be part of the same paragraph. The margin is specified "
             "relative to the height of a line.")
    la_params.add_argument(
        "--boxes-flow", "-F", type=float_or_disabled, default=0.5,
        help="Specifies how much a horizontal and vertical position of a "
             "text matters when determining the order of lines. The value "
             "should be within the range of -1.0 (only horizontal position "
             "matters) to +1.0 (only vertical position matters). You can also "
             "pass `disabled` to disable advanced layout analysis, and "
             "instead return text based on the position of the bottom left "
             "corner of the text box.")
    la_params.add_argument(
        "--all-texts", "-A", default=False, action="store_true",
        help="If layout analysis should be performed on text in figures.")

    output_params = parser.add_argument_group(
        'Output', description='Used during output generation.')
    output_params.add_argument(
        "--outfile", "-o", type=str, default="-",
        help="Path to file where output is written. "
             "Or \"-\" (default) to write to stdout.")
    output_params.add_argument(
        "--output_type", "-t", type=str, default="text",
        help="Type of output to generate {text,html,xml,tag}.")
    output_params.add_argument(
        "--codec", "-c", type=str, default="utf-8",
        help="Text encoding to use in output file.")
    output_params.add_argument(
        "--output-dir", "-O", default=None,
        help="The output directory to put extracted images in. If not given, "
             "images are not extracted.")
    output_params.add_argument(
        "--layoutmode", "-Y", default="normal",
        type=str, help="Type of layout to use when generating html "
                       "{normal,exact,loose}. If normal,each line is"
                       " positioned separately in the html. If exact"
                       ", each character is positioned separately in"
                       " the html. If loose, same result as normal "
                       "but with an additional newline after each "
                       "text line. Only used when output_type is html.")
    output_params.add_argument(
        "--scale", "-s", type=float, default=1.0,
        help="The amount of zoom to use when generating html file. "
             "Only used when output_type is html.")
    output_params.add_argument(
        "--strip-control", "-S", default=False, action="store_true",
        help="Remove control statement from text. "
             "Only used when output_type is xml.")
    return parser


# main


def main(args=None):

    P = maketheparser()
    A = P.parse_args(args=args)

    if A.page_numbers:
        A.page_numbers = {x-1 for x in A.page_numbers}
    if A.pagenos:
        A.page_numbers = {int(x)-1 for x in A.pagenos.split(",")}

    if A.output_type == "text" and A.outfile != "-":
        for override, alttype in OUTPUT_TYPES:
            if A.outfile.endswith(override):
                A.output_type = alttype

    res = extract_text(**vars(A))
    (outfp, info) = res
    outfp.close()
    from xml.etree import ElementTree as etree
    document = etree.parse(outfp.name)
    #document = etree.parse( '/home/nulysses/Downloads/pdf_test/pdf_extract/2021-07-21_11-39-07/Bomito-1315137 - Strato AG.pdf.xml')
    root = document.getroot()
    elem1 = etree.Element('Document')
    elem1.text = '\n'
    elem1.tail = '\n'
    elem2 = etree.SubElement(elem1, 'DocInfo')
    elem2.text = '\n'
    elem2.tail = '\n'
    title = etree.SubElement(elem2, 'Title')
    title.text = ''
    if 'Title' in info:
        title.text = decode(info['Title'])
    title.tail = '\n'
    producer = etree.SubElement(elem2, 'Producer')
    producer.text = ''
    if 'Producer' in info:
        producer.text = decode(info['Producer'])
    producer.tail = '\n'
    creator = etree.SubElement(elem2, 'Creator')
    creator.text = ''
    if 'Creator' in info:
        creator.text = decode(info['Creator'])
    creator.tail = '\n'
    creation_date = etree.SubElement(elem2, 'CreationDate')
    creation_date.text = ''
    if 'CreationDate' in info:
        creation_date.text = decode(info['CreationDate'])
    creation_date.tail = '\n'
    root.insert(0, elem1)
    for page in root:
        words = page.findall('word')
        for word in words:
            page.remove(word)
        texts = page.findall('text')
        for text in texts:
            page.remove(text)
        if words:
            page.extend(words)
        if texts:
            page.extend(texts)
        figures = page.findall('figure')
        for figure in figures:
            words = figure.findall('word')
            for word in words:
                figure.remove(word)
            texts = figure.findall('text')
            for text in texts:
                figure.remove(text)
            if words:
                figure.extend(words)
            if texts:
                figure.extend(texts)
        textboxes = page.findall('textbox')
        for textbox in textboxes:
            textlines = textbox.findall('textline')
            for textline in textlines:
                words = textline.findall('word')
                for word in words:
                    textline.remove(word)
                texts = textline.findall('text')
                for text in texts:
                    textline.remove(text)
                if words:
                    textline.extend(words)
                if texts:
                    textline.extend(texts)
    document.write(outfp.name, short_empty_elements=False)
    return 0
encodings = [
    "utf-8",
    "utf-8-sig",
    "utf-16",
    "cp1252",
    "ascii"
]
def decode_helper(string):
  for encoding in encodings:
    try:
      return [string.decode(encoding), encoding]
    except UnicodeDecodeError:
      pass

def decode(string):
  ret = decode_helper(string)
  ret = str(ret[0].encode("utf-8"), "utf-8")
  return ret


if __name__ == '__main__':
    sys.exit(main())
