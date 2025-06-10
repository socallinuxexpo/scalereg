#!/usr/bin/env python3

import datetime
from PIL import Image, ImageDraw, ImageFont
import os
import subprocess


class Badge:
  def __init__(self, data, datadir):
    self.datadir = datadir

    tickets = {
      'expo': 'Enthusiast',
      'full': 'Supporter',
      'press': 'Press',
      'speaker': 'Speaker',
      'exhibitor': 'Exhibitor',
      'staff': 'Staff',
      'friday': 'Friday Only',
    }

    badge_data = data.split('~')[1:-1]
    if len(badge_data) < 14:
      raise ValueError
    self.salutation = badge_data[0]
    self.first_name = badge_data[1]
    self.last_name = badge_data[2]
    self.full_name = '%s %s' % (self.first_name, self.last_name)
    self.title = badge_data[3]
    self.company = badge_data[4]
    self.email = badge_data[5]
    self.phone = badge_data[6]
    self.zip = badge_data[7]
    self.id = int(badge_data[8])
    self.hash = badge_data[9]
    self.reprint = int(badge_data[10])
    self.type = tickets[badge_data[11]]
    self.amount = badge_data[12]
    self.shirt = badge_data[13]
    self.addons = badge_data[14:]
    self.data = '%s' % '~'.join(
        [str(self.id) + self.hash, self.first_name, self.last_name, self.title,
         self.company, self.phone, self.zip, self.email])

  def printBadge(self):
    badge_file = os.path.join(self.datadir,
                              'out_png',
                              '%05d_%d.png' % (self.id, self.reprint))
    if os.path.exists(badge_file):
      return
    out_image = self.genBadge()
    if out_image:
      out_image.save(badge_file, 'PNG')

  def putText(self, outimage, font_name, initial_fontsize, text, x, y, container_width, align_right):
    fontfile = os.path.join(self.datadir, 'fonts', '%s.ttf' % font_name)
    fontsize = initial_fontsize
    draw = ImageDraw.Draw(outimage)

    while True:
      image_font = ImageFont.truetype(fontfile, fontsize)
      # Get bounding box: (x1, y1, x2, y2)
      # x1, y1 are generally 0,0 if text starts at (0,0) relative to its own box for textbbox
      # For textlength, it gives total width.
      # For textbbox, (x_offset, y_offset, width+x_offset, height+y_offset)
      bbox = draw.textbbox((x,y), text, font=image_font)
      text_width = bbox[2] - bbox[0] # x2 - x1

      if text_width > container_width and fontsize > 2: # Ensure fontsize doesn't become too small
        fontsize -= 2
      else:
        current_x = x
        if align_right:
          current_x = x + container_width - text_width
        draw.text((current_x, y), text, font=image_font, fill=(0,0,0))
        break

  def genBadge(self):
    print('generating badge for code: %05d' % self.id)
    try:
      # generate barcode
      barcode_script = os.path.join(self.datadir, 'barcode.sh')
      barcode_out_dir = os.path.join(self.datadir, 'out_barcodes')
      os.makedirs(barcode_out_dir, exist_ok=True) # Ensure directory exists
      barcode_out = os.path.join(barcode_out_dir, '%05d.png' % self.id)

      barcode_type="dummy" # This might need to be a valid type for barcode.sh
      process = subprocess.Popen([barcode_script, barcode_out, self.data, barcode_type])
      (_, ret) = os.waitpid(process.pid, 0) # Using waitpid is more robust
      if ret != 0:
        print(f"Barcode generation failed for {self.id} with ret code {ret}")
        return None

      # open image template
      out_image = Image.open(os.path.join(self.datadir, 'badge.png'))

      # get and paste barcode
      if not os.path.exists(barcode_out):
          print(f"Barcode file {barcode_out} not found for {self.id}")
          return None
      barcode_image = Image.open(barcode_out)

      barcode_left = 2100
      barcode_bottom = 2650
      imageHeight = barcode_image.size[1] # size is (width, height)
      barcode_top = barcode_bottom - imageHeight
      out_image.paste(barcode_image, (barcode_left, barcode_top))

      main_top = barcode_bottom + 200 
      main_left = 1600 - 50 
      main_width = 800

      # print out name
      self.putText(out_image, 'arialbd', 72, self.full_name, main_left, main_top,
                   main_width, True)
      
      # print out receipt (These seem to be for a different part of the badge, adjust coordinates as needed)
      # Assuming receipt_left, receipt_top, receipt_width are defined or adjusted from main_left etc.
      receipt_left = main_left - 1660
      # self.putText(out_image, 'arialbd', 36, "Name: " + self.full_name, receipt_left, main_top, main_width, False)
      # self.putText(out_image, 'arialbd', 36, "Ticket Type: " + self.type, receipt_left, main_top+60, main_width, False)
      # self.putText(out_image, 'arialbd', 36, "Paid: " + self.amount, receipt_left, main_top + 120, main_width, False)


      # print out title
      main_top = main_top + 100
      self.putText(out_image, 'arial', 42, self.title, main_left, main_top,
                   main_width, True)

      # print out company
      main_top = main_top + 100
      self.putText(out_image, 'arial', 42, self.company, main_left, main_top,
                   main_width, True)

      # print id
      side_left = 1350
      side_top = 3100
      side_width = 200
      #self.putText(out_image, 'arial', 20, '#' + str(self.id), side_left, side_top,
      #             side_width, False)

      # print out badge type
      side_top = side_top - 80
      self.putText(out_image, 'arialbd', 48, self.type, side_left, side_top,
                   side_width, False)
      

      return out_image
    except Exception as e: # Catch specific exceptions if possible
      print(f'failed for badge for code: {self.id}, error: {e}')
      # raise # Uncomment if you want to see the full traceback during debugging
      return None


def fetchDB(datadir):
  #return realFetchDB(datadir)
  return fakeFetchDB(datadir).split('\n')


def realFetchDB(datadir):
  # This function expects attendees.txt to exist.
  # For testing, ensure this file is present or use fakeFetchDB.
  try:
    with open(os.path.join(datadir, 'attendees.txt'), 'r') as r:
      return r.readlines() # Readlines will give a list of lines
  except FileNotFoundError:
    print("attendees.txt not found, using fake data.")
    return fakeFetchDB(datadir).split('\n')


def fakeFetchDB(datadir):
  print("Using fake data, see fetchDB()")
  return """~Mr.~John~Doe~Title~Company~sdf@asdf.com~555-555-1212~1~0~expo~130.00~???~~
~Salutation~First Name~Last Name~Title~Company~Email~Phone~1324~0~friday~100.00~Large~Foo~Bar~Qux~XYZZY 12345~
~Mr.~Lei~Zhang~Slacker~Home~leiz@example.org~6261234567~555~0~staff~50~Medium~
~Mr.~John Billy~Scott~President~ACME Incorporated~president@acme.inc~1234567890~999~1~expo~10~Medium~"""

def printRun():
  print('Starting print run at %s' % datetime.datetime.today().isoformat(' '))

  datadir = os.getcwd() # Assuming script is run from the 'print' directory
  # Ensure 'out_png' directory exists
  os.makedirs(os.path.join(datadir, 'out_png'), exist_ok=True)

  attendees = fetchDB(datadir)

  for att_line in attendees:
    att = att_line.strip() # Remove newline characters if reading from file
    if not att: # Skip empty lines
        continue
    try:
      badge = Badge(att, datadir)
      badge.printBadge()
    except ValueError as ve:
      print(f'Could not generate badge for {att}, ValueError: {ve}')
      continue
    except Exception as e:
      print(f'An unexpected error occurred for {att}: {e}')
      continue


  print('done')


if __name__ == '__main__':
  printRun()
