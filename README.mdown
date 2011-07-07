
# fireproof.py

Fireproof is a static website generator. It's not tied to a specific type of
website (like many static *blog* generators), but can be used to create many
different types of sites.

A site is made much like a plain HTML site would be made. All your content is
put in a single root directory that represents your site. The directory
structure is up to you. But fireproof allows you to use custom page types for
all of your textual content, using YAML for metadata and markdown for the body
of the page. That content can then be rendered and filtered using templates.

When you're ready to deploy your site, invoke fireproof, and it will render your
templates and copy all the content to the output directory that you specify.

## An Example

Suppose you want to make a blog, which is made up of multiple entries. And you
also want a home page to display links to your entries. It's pretty easy.

First, you write a sample entry and save it as `/my-first-entry.entry`:

    title: My First Blog Entry
    date:  !!timestamp 2011-04-26 11:24:00 -3
    
    Hi Everyone! Welcome to my blog!

Metadata at the top, using YAML; content after an empty line, using markdown.

Fireproof will simply copy this as a static file until you define a template
for it. The name of the template should be the page type (here `entry`) with the
desired extension of the output, and it must be in the `/templates/` directory.

We want our blog entries to be saved as `.html`, so we'll create a template,
`/templates/entry.html`:

    <html>
      <head>
        <title>{{ entry.title }} ({{ entry.date|strftime("%B %d) }})</title>
      </head>
      <body>{{ entry }}</body>
    </html>

Now fireproof knows to process all our `.entry` files as templated pages.

You probably also want to create a home page. Create an empty file,
`/index.home`, and a template for it, `templates/home.html`.

In your template, you want to list out the 10 most recent entries:

    <html>
      <head><title>My Site</title></head>
      <body>
      <ul>
      {# pages() is a function provided by fireproof--documentation is provided below #}
      {% for entry in pages(site, types=['entry'], order_by=['-date'], limit=10) %}
        <li><a href='{{ entry.url }}'>{{ entry.title }}</a></li>
      {% endfor %}
      </ul>
      </body>
    </html>

Pretty simple! It's not too much harder move your entries into subdirectories
based on year and month and provide archives of all your entries.

If you want to add more complicated markup for the entries—and share it between
the individual pages and main index—you can move the logic into a _partial_
template.

Create `templates/_entry.html`:

    <h1>{{ entry.title }}</h1>
    {{ entry.text }}

Now `{{ entry }}` will return the value of this partial template in the other
templates.

If you create a partial for a page type but don't create a normal template, you
can create a default template and use the value of a partial. Since all pages
are pages, this default template should be called `page.ext`.

So create `templates/page.html`:

    <html>
      <head>
        <title>{{ page.title }} ({{ page.date|strftime("%B %d) }})</title>
      </head>
      <body>{{ page }}</body>
    </html>

Now `templates/entry.html` can be deleted.

## The Site

The site object contains only one real standard property. Any other properties
that you want to define can be added to a YAML file named `.fireproof` inside
your root site directory. The properties defined in that file will be added
directly to the site object. This is handy for some values, like the site's
title, author, and URL.

### Standard Properties

  * `directory`
  
  The directory on disk where the site is found.
  
  * `url`
  
  This property is not defined by fireproof, but it is recommended that you
  define it.

## Pages

Pages follow a simple format on disk: YAML, followed by an empty line, and
a markdown body. The body is optional. Any properties defined in the YAML will
be added directly to the page object.

In templates, Pages stringify to their `text` property.

### Standard Properties 

  * `absolute_url`
  
    The absolute URL of the page. This is a combination of `page.site.url` and
    `page.url`, so if you want to use it, you need to define a url for the site.
  
  * `directory`
  
    The directory on the site that contains the output for the page.
  
  * `file`
  
    The name of the output file, relative to the output directory.
  
  * `path`
  
    The path of the file on disk that the page is created from, relative to the
    site directory.
  
  * `site`
  
    The site object that the page belongs to.
  
  * `tag`
  
    A Atom-style tag URI for the page, created for use in Atom feeds.
  
  * `text`
  
    The HTML (markdown-converted) content of the page.
  
  * `type`
  
    The page type of this page. Fer `my-first-post.entry`, this would equal
    `entry`.
  
  * `url`
  
    The URL of the page in the form `/foo/bar.baz`.

## Templates

Templates are created using [Jinja2][]. You can go look at
[their documentation][] for template designers, as it all applies directly to
fireproof.

[Jinja2]: http://jinja.pocoo.org/
[their documentation]: http://jinja.pocoo.org/docs/templates/

Of course, fireproof provides some items of its own for you to use.

### Variables

#### `site`

The site that the current page is a part of. See the documentation above for
more information about sites.
 
#### `page` (or *`page-type`*)

The current page. It is available both as `page` and as the same name of your
page type. So for `my-new-blog.entry`, `entry` would be a synonym for `page`.
See the documentation above for more information about pages.

#### `now`

The current time, which can be formatted with `strftime`.

### Functions

#### `pages(site, types=[], directory=None, limit=None, order_by=[])`
   
This is the main workhorse of fireproof. It returns a list of page objects that
match the parameters.

  * `site` is the Site object that is present on every page
  * `types` is a list of your custom defined page types
  * `directory` limits the search to pages from a certain directory
  * `limit` will limit the number of pages that are returned
  * `order_by` specifies the sort order for the objects that are returned. It is
    a list of attributes from the page objects. Including a `-` at the beginning
    of the key will reverse the order. Pages will be sorted by the first key and
    any ties will be broken by subsequent keys.

If you had a normal blog setup, with separate directories for each year and
subdirectories for each month that contain the actual entries, you could display
all the posts in a year or month for an archive page like so:

    <ul>
    {% for p in pages(site, types=['post'], directory=page.directory, order_by=['-date']) %}
        <li>{{ p.title }}</li>
    {% endfor %}
    </ul>

You could show the 10 most recent posts for a the homepage like so:

    <ul>
    {% for p in pages(site, types=['post'], limit=10, order_by=['-date']) %}
        <li>{{ p.title }}</li>
    {% endfor %}
    </ul>

### Filters

#### `rfc3339`

This filter formats dates in the format specified by RFC 3339. This was added
specifically for generating Atom feeds.

    {{ page.date | rfc3339 }}

#### `strftime`

The `strftime` function, provided by Python's `datetime` module, is provided as
a filter for formatting dates. Refer to the official [strftime documentation][]
for more information on how to use it.

[strftime documentation]: http://docs.python.org/library/datetime.html#strftime-and-strptime-behavior

    {{ page.date | strftime("%B %d") }}

## TODO

#### Add more ways to ignore files, using a Site property and .gitnore
#### Add a notion of drafts
#### Add a template function to retrieve other types of files, like images
#### Add examples
#### Make the template directory configurable
#### Support for sites that don't exist at the domain root
#### Pagination
#### A way to add tags
