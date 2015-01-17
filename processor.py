__author__ = 'kpellegr'


import random
import subprocess
import glob
import string
import os

def get_documents(folder='input', pattern='*.pdf'):
    docList = []
    pattern = os.path.join(folder, pattern)

    for docfile in glob.glob(pattern):
        docList.append(docfile)

    return docList

def get_number_of_pages(doc):
    res = subprocess.check_output(['./pdfpages.sh', doc])
    return int(res.strip())

def is_single_divider(doc, page_num):
    return compare_document(doc, page_num, 'single.pdf', 1) > 0.1

def is_multi_divider(doc, page_num):
    return compare_document(doc, page_num, 'multi.pdf', 1) > 0.1

def compare_document(doc1, page1, doc2, page2):
    docname1 = "{0}[{1}]".format(doc1, page1 - 1)
    docname2 = "{0}[{1}]".format(doc2, page2 - 1)
    res = subprocess.check_output(['compare', '-colorspace', 'Gray', '-metric', 'ncc', docname1, docname2, '/tmp/diff.png'], stderr=subprocess.STDOUT)
    res = res.strip()
    print "Compare %s %s returned %s" % (docname1, docname2, res)
    return float(res)


def split_document(input_name):
    #Constants to maintain state
    cSINGLE = 1
    cMULTI = 2

    #Internal variables
    current_state = cSINGLE
    current_ptr = 1
    start_ptr = current_ptr
    is_divider = False
    new_doc_list= []

    print "---------------"
    number_of_pages = get_number_of_pages(input_name)
    print "Processing %s (%d)" % (input_name , number_of_pages)

    while current_ptr <= number_of_pages:
        print "Processing page %d" % (current_ptr)
        if is_single_divider(input_name, current_ptr):
            print "Found SINGLE divider on page %d" % (current_ptr)
            current_state = cSINGLE
            is_divider = True
        elif is_multi_divider(input_name, current_ptr):
            print "Found MULTI divider on page %d" % (current_ptr)
            current_state = cMULTI
            is_divider = True
        else:
            print "Found content page on page %d" % (current_ptr)
            is_divider = False

        if is_divider:
            if (start_ptr <= current_ptr) and (current_ptr > 1):
                print "Splitting off pages %d to %d" % (start_ptr, current_ptr - 1)
                new_doc_list.append({'parent': input_name, 'start': start_ptr, 'end': current_ptr - 1})
            current_ptr += 1
            start_ptr = current_ptr
        else:
            if (current_state == cSINGLE) or (current_ptr == number_of_pages):
                print "SINGLE: Splitting off pages %d to %d" % (start_ptr, current_ptr)
                new_doc_list.append({'parent': input_name, 'start': start_ptr, 'end': current_ptr})
                current_ptr += 1
                start_ptr = current_ptr
            else:
                print "MULTI: moving on..."
                current_ptr += 1
    return new_doc_list

def save_documents(doclist):
    for doc in doclist:
        range_str = '[{0}-{1}]'.format(int(doc['start']) - 1 , int(doc['end']) - 1)
        input_name = doc['parent'] + range_str

        base = classify_document(doc['parent'], doc['start'])
        garble = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(16))
        output_name = os.path.join('output', '{0}-{1}-{2}.pdf'.format(base, str(doc['start']).zfill(3), garble))

        print "Executing convert %s %s" % (input_name, output_name)
        subprocess.call(['convert', '-density', '150', input_name, output_name])

def classify_document(doc_name, page_number):
    accuracy = 0.3    
    ref_list = get_documents('refs');
    
    for ref_doc in ref_list:
        if compare_document(doc_name, page_number, ref_doc, 1) >= accuracy: #only compare the first page
            base =  os.path.basename(ref_doc).split('-')[0]
            print "Found a match with {0}, classifying as {1}".format(ref_doc, base);
            return base;
    
    # no match found
    return "unknown" 


# ======================================
# ======================================
for input_name in get_documents():
    new_doc_list = split_document(input_name)
    save_documents(new_doc_list)
