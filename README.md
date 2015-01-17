#Processor

## What it does

Processor.py is a Python script to process scanned (or downloaded) bundles of invoices and classify them automatically. The script implements a three-step process:
1. Split the pdf into invoices, based on separation pages marked *multi* or *1*. *multpi* means that the following pages all belong together and should be treated aa a single invoice (e.g. Base or Telenet).
The marker *1* indicates that the next set of pages should al be treated individually. Each page is a separate invoice.
2. Classify each invoice under the correct supplier. This is done by comparing each invoice (or the first page, in case of *multi*-dcouments) with a set of reference invoices. _Note: Currently this
matching process is implemented naively: every document is compared to the reference documents. A match is declared as soon as the correlation between the two documents is over a threshold value. We use the
ncc metric in ImageMagick to compare the documents:_ `compare -metric ncc page1.pdf page2.pdf output.png`
3. Based on the supplier, we prepare metadata for the invoice, so that it can be sent to Exact Online. The metadata includes description, booking lines, VAT. _Note: This third step has not been implemented yet._

## Requirements

### ImageMagick

The main requirement is ImageMagick. The script uses system calls to call ImageMagick's "convert" and "compare" commands.

`convert -density 150 scanned_doc.pdf[2-3] telenet-653GDG.pdf`

This command extracts pages 2 to 3 (actually pages 3 to 4 because the index is zero-based) from the scanned document and creates a new pdf with the name telenet-653GDG.pdf. The image will be
converted at 150dpi (which is more than reasonable for image recognition and for human reading).

`compare -metric ncc page1.pdf[2] multi.pdf output.png

Compares the third pages of page1.pdf with the multi-separator page. Output.png is an obligatory parameter, but is not used. This command returns a single number between 0 and 1 which denotes the
correlation between the two images (1 is an exact match).

 ### pdfinfo

 pdfinfo is a command found on most Linux distributions. In this case, we use it (within the pdfpages.sh shell script) to extract the number of pages from a pdf


## Usage

Right now, the script is not very robust (breaks down when not everything is perfect) and not flexible (doesn't have any input parameters). It will scan a folder called _input_ for scanned
pdf documents and process them one-by-one. It will look in the current directory for _multi.pdf_ and _single.pdf_ (the separator pages). Reference invoices, used for automatic classification
 should be in the _refs_ subdir and the document name should start with the supplier (e.g. telenet-2.pdf). Note that it is ok to have more than one reference document per supplier. The script will just
 look for a match over a particular threshold.
 Lastly, the script will put the classified pdf in the _output_ folder.

 # Improvements

## Robustness

The script breaks whenever something goes wrong. We need more elegant error-handling and also determine errors from which we can recover (e.g. the script shouldn't crash because
we fail to convert one of the documents).

The 'compare' function requires two documents of the same image size (pixels and resolution). This is currently not handled correctly. If the source is exactly the same (e.g. both
the invoice and the comparison document where scanned), everyhting works fine. However, even the slightest difference causes the script the fail (e.g. comparing a scanned pdf
to a downloaded pdf or comparing a colour document to a black-and-white pdf). 

## Flexibility

Right now, the script has some parameters hard-coded into it, such as input folder and output folder. It is probably a good idea to make it more configurable to cope with more varied
environments.

## Bookings

The third step of the script would be to have a configuration file which lists all metadata per supplier. The file should contain a default description and default booking lines for the supplier.
When a document is classified, we prepare a booking for that document for Exact Online.

## Integration with a database

If we look at the future, we may want to _enrich_ the document metadata. It may be useful to keep the documents (or references to them) and the metadata in a simple database. The same
database can be used to power a script that actually injects the documents and the bookings into Exact Online.

## More intelligent document matching
Right now, the processor matches the reference documents quite naively: it will process the reference invoices one by one and stop at the first match over a particular threshold (currently at 0.3). This
strategy can cause problems when reference invoices look very much alike, or when invoices form the same supplier differ greatly (e.g. a small versus a small number of invoice lines).

A smarter strategy could be to implement multiple thresholds. For example if the correlation is over 0.5, then we classify the document immediately. If the threshold is under 0.1, it is rejected
immediately. If the correlation is between 0.5 and 0.1, then we keep comparing the document to all other reference documents. If we find a better match (over 0.5), we classify again. Otherwise, we keep
processing all reference invoices (and we keep all matches between 0.1 and 0.5).
When all invoices are processed, we have an array with suppliers who all matched between 0.1 and 0.5. If the array contains only a single supplier, we have a match, if the array contains multiple suppliers,
the match is indecisive and the documents should be classified as _unkown_.
