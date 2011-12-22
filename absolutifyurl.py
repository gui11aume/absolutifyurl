# -*- coding: utf-8 -*-

import os
import re
import cgi
import urllib2
import urlparse

from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app


class MainHandler(webapp.RequestHandler):
   def get(self):
      dot = os.path.dirname(__file__)

      # Fill in the HTML page...
      template_path = os.path.join(dot, 'absolutifyurl_template.html')
      template_values = {
         'page_title': 'Absolutify URL',
         'page_content': open(os.path.join(
                               dot,
                               'content',
                               'upload_content.html'
                         )).read()
      }
      
      # ... and send!
      self.response.out.write(
            template.render(template_path, template_values)
      )


class UploadHandler(webapp.RequestHandler):

   def get_base(self, url):
      """Return the base of a queried url."""

      parsed_url = urlparse.urlparse(url)

      return urlparse.urlunparse((
            parsed_url.scheme,
            parsed_url.netloc,
            re.sub('[^/]*$', '', parsed_url.path),
            '',
            '',
            '',
      ))


   def post(self):
      url = self.request.get('url')
      try:
         followed_url = urllib2.urlopen(url)
      except Exception:
         self.redirect('/')
         return

      base = self.get_base(followed_url.geturl()) 

      def rebase_html(match):
         """Rebase 'src', 'href' and 'background' attributes
         from HTML data."""
         (attr, quote) = match.groups()[:2]
         new_url = urlparse.urljoin(base, match.groups()[3], True)
         return "%s=%s%s%s" % (attr, quote, new_url, quote)

      def rebase_css(match):
         """Rebase the 'url' attribute from <style> tag content."""
         return re.sub(
            '(?i)url\s*\((.*?)\)',
            'url(' + urlparse.urljoin(base, '\\1', True) + ')',
            match.groups()[0]
         )

      # Rebase 'src' and 'href' attributes
      html = re.sub(
                 '(?i)(src|href|background)=(["\'])(?!http://)(/)?(.*?)\\2',
                 rebase_html,
                 followed_url.read().decode('utf-8', 'ignore')
             )

      # Rebase 'url' attribute in <style> tag content.
      html = re.sub(
                 '(?si)(<style.*?</style>)',
                 rebase_css,
                 html
             )

      msg = html if self.request.get('test') else \
            '<html><head><title>%s</title></head><pre>%s</pre></html>' % \
            ('Your absolutified source' , cgi.escape(html))

      # Et voila!
      self.response.out.write(msg)


def main():
   application = webapp.WSGIApplication(
        [('/', MainHandler),
         ('/upload', UploadHandler),
        ], debug=True)
   run_wsgi_app(application)

if __name__ == '__main__':
   main()
