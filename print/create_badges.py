#!/usr/bin/python

import datetime
import gd
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
    if len(badge_data) < 11:
      raise ValueError
    self.salutation = badge_data[0]
    self.first_name = badge_data[1]
    self.last_name = badge_data[2]
    self.full_name = '%s %s' % (self.first_name, self.last_name)
    self.title = badge_data[3]
    self.company = badge_data[4]
    self.email = badge_data[5]
    self.phone = badge_data[6]
    self.id = int(badge_data[7])
    self.type = tickets[badge_data[8]]
    self.amount = badge_data[9]
    self.addons = badge_data[11:]
    self.data = '%s' % '~'.join(
      [str(self.id), self.first_name, self.last_name, self.title, self.company, self.phone, self.email])

  def printBadge(self):
    badge_file = os.path.join(self.datadir, 'out_png', '%05d.png' % self.id)
    if os.path.exists(badge_file):
      return
    out = self.genBadge()
    if out:
      out.writePng(badge_file)

  def putText(self, outimage, font, fontsize, text, x, y, width, align):
    fontfile = os.path.join(self.datadir, 'fonts', '%s.ttf' % font)
    while True:
      right = outimage.get_bounding_rect(fontfile, fontsize, 0, (x,y), text)[4]
      if right > x + width:
        fontsize = fontsize - 2
      else:
        if align:
          x = x + width - (right - x)
        break
    outimage.string_ft(fontfile, fontsize, 0, (x,y), text, 0)

  def genBadge(self):
    print 'generating badge for code: %05d' % self.id
    try:
      # generate barcode
      barcode_script = os.path.join(self.datadir, 'barcode.sh')
      barcode_out = os.path.join(self.datadir, 'out_barcodes',
                                 '%05d.png' % self.id)
      barcode_type="dummy"
      process = subprocess.Popen([barcode_script, barcode_out, self.data, barcode_type])
      (_, ret) = os.waitpid(process.pid, 0)
      if ret != 0:
        return None

      # open image template
      out = gd.image(os.path.join(self.datadir, 'badge.png'))

      # get and paste barcode
      barcode = gd.image(barcode_out)
      barcode_left = 2100
      barcode_bottom = 2650
      imageHeight = barcode.size()[1]
      barcode_top = barcode_bottom - imageHeight
      barcode.copyTo(out, (barcode_left, barcode_top))

      main_top = barcode_bottom + 200 
      main_left = 1600 - 50 
      main_width = 800

      # print out name
      self.putText(out, 'arialbd', 72, self.full_name, main_left, main_top,
                   main_width, True)
      
      # print out receipt
      self.putText(out, 'arialbd', 36, "Name: " + self.full_name, main_left - 1660, main_top, main_width, True) 
      self.putText(out, 'arialbd', 36, "Ticket Type: " + self.type, main_left - 1650, main_top+60, main_width, True)
      self.putText(out, 'arialbd', 36, "Paid: " + self.amount, main_left - 1650, main_top + 120, main_width, True)

      # print out title
      main_top = main_top + 100
      self.putText(out, 'arial', 42, self.title, main_left, main_top,
                   main_width, True)

      # print out company
      main_top = main_top + 100
      self.putText(out, 'arial', 42, self.company, main_left, main_top,
                   main_width, True)

      # print id
      side_left = 1350
      side_top = 3100
      side_width = 200
      #self.putText(out, 'arial', 20, '#' + str(self.id), side_left, side_top,
      #             side_width, False)

      # print out badge type
      side_top = side_top - 80
      self.putText(out, 'arialbd', 48, self.type, side_left, side_top,
                   side_width, False)
      

      return out
    except:
      print 'failed for badge for code: %05d' % self.id
      raise
      return None


def fetchDB(datadir):
  #return realFetchDB(datadir)
  return fakeFetchDB(datadir).split('\n')


def realFetchDB(datadir):
  r = open(os.path.join(datadir, 'attendees.txt'))
  return r


def fakeFetchDB(datadir):
  print "Using fake data, see fetchDB()"
  return """~Salutation~First Name~Last Name~Title~Company~Email~Phone~1324~friday~100~Large~Foo~Bar~Qux~XYZZY 12345~
~Mr.~Lei~Zhang~Slacker~Home~leiz@example.org~6261234567~555~staff~50~Medium~
~Mr.~John Billy~Scott~President~ACME Incorporated~president@acme.inc~1234567890~999~expo~10~Medium~"""


def printRun():
  print 'Starting print run at %s' % datetime.datetime.today().isoformat(' ')

  datadir = os.getcwd()
  attendees = fetchDB(datadir)

  for att in attendees:
    try:
      badge = Badge(att, datadir)
      badge.printBadge()
    except ValueError:
      print 'Could not generate badge for %s' % att
      continue

  print 'done'


if __name__ == '__main__':
  printRun()
