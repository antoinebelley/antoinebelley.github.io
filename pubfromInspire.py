import requests
import os
import re

API_URL = "https://inspirehep.net/api/literature?q=a%20Antoine.Belley.1&size=50"


def latex_to_matjax(title):
    #Replace the latex $...$ delimiter by the mathjax \\(... \\) delimiter
    indices = [i for i, char in enumerate(title) if char == "$"]
    id_even = indices[::2]
    id_odd = indices[1::2]
    latex_eq = False
    title = list(title)
    for i, char in enumerate(title):
        #If inside a latex equation, chages \ for \\
        #Further replace spaces by ~
        if latex_eq:
            if char == "\\":
                title[i] = r"\\"
            elif char == " ":
                title[i] = "~"
        if i in id_even:
            title[i] = r"\\("
            latex_eq = True
        elif i in id_odd:
            title[i] = r"\\)"
            latex_eq = False
    title = "".join(title)
    #Remove things that can cause issue in the titles like string pattern that 
    # have a "" inside of them
    title = re.sub(r' display="inline"', '', title)
    return title


def update_publications():
    response = requests.get(API_URL).json()
    hits = response.get('hits', {}).get('hits', [])

    for hit in hits:
        meta = hit['metadata']
        if {meta.get('arxiv_eprints', [{}])[0].get('value', '')}=="": continue
        # Extract Data
        title = meta['titles'][0]['title']
        title = latex_to_matjax(title)
        date = meta.get('preprint_date') or meta.get(
            'publication_info', [{}])[0].get('year', '2024')
        year = str(date)[:4]
        if date == 2024:
            date = "2024-08-23"
        # Handle Authors (Highlighting your name)
        if len(meta.get('authors', [])) > 10:
            authors = [a['full_name'] for a in meta.get('authors', [])[:10]]
            print(authors)
            authors.append("et al.")
        else:
            authors = [a['full_name'] for a in meta.get('authors', [])]
        author_str = ", ".join(authors)
        author_str = author_str.replace(
            "Belley, Antoine", "<span class='highlight'>Belley, Antoine</span>")
        author_str = author_str.replace(
            "Belley, A.", "<span class='highlight'>Belley, A.</span>")
        # Gets number of citations
        citation_count = meta["citation_count"]
        # Determine Badge (e.g., PRL, arXiv, etc.)
        venue = meta.get('publication_info', [{}])[
            0].get('journal_title', 'arXiv')
        badge = "pub-badge-arxiv"
        if "Phys.Rev.C" in venue:
            badge = "pub-badge-PRL"
        if "Phys.Rev.Lett." in venue:
            badge = "pub-badge-PRL"
        if title == "Probing beyond standard model physics through ab initio calculations of exotic weak processes in atomic nuclei":
            venue = "Thesis"
            badge = "UBC"
        #Get link to the first figure of the paper
        try:
          figure_link = meta['figures'][0]['url']
          figure_name = meta['figures'][0]['filename']
        except:
          figure_link = ""
          figure_name = ""
        # Chooses tags for the paper
        topics = []
        #Check if the paper has been submitted to nucl-ex
        arxiv_category = meta.get("primary_arxiv_category")
        if arxiv_category == None:
            arxiv_category = [""]
        if arxiv_category[0] == 'nucl-ex':
            topics.append("Experiment")
        #Check if the paper contains any terms related to 0vbb
        keywords = ['neutrinoless', 'beta', 'weak processes', 
                    '<math><mrow><mn>0</mn><mi>ν</mi><mi>β</mi><mi>β</mi></mrow></math>']
        for string in keywords:
            if re.search(string, title, re.IGNORECASE):
                topics.append("0vbb")
                break
        # Check if paper is related to symmetry-breaking
        keywords = ['symmetry-breaking', 'parity-violation', 'schiff moment', 'anapole', 'electroweak']
        for string in keywords:
            if re.search(string, title, re.IGNORECASE):
                topics.append("Symmetry-breaking")
                break
        # Check if paper is related to nuclear-structure
        keywords = ['shell', 'radius', 'radii', 'spectruc', 'spectra', 'moments',
                    'moment', 'electromagnetic',
                    'Global Framework for Emulation of Nuclear Calculations']
        for string in keywords:
            if re.search(string, title, re.IGNORECASE):
                topics.append("Structure")
                break
        # Check if paper is related to emulator
        keywords = ['emulator', 'machine-learning', "AI ", 'Framework', 'emulation',
                    'Nuclear charge radii of aluminium isotopes at the proton drip line',
                    'Probing beyond standard model physics through ab initio calculations of exotic weak processes in atomic nuclei',
                    'Uncertainty Quantification', 
                    'Correlation of <math><mrow><mn>0</mn><mi>ν</mi><mi>β</mi><mi>β</mi></mrow></math> decay nuclear matrix elements with nucleon-nucleon phase shifts']
        for string in keywords:
            if re.search(string, title, re.IGNORECASE):
                topics.append("Emulation")
                break
        # Construct the Markdown
        content = f"""---
title: "{title}"
date: {date}
venue: "{venue}"
venue_badge: "{badge}"
authors: "{author_str}"
topics: {topics} # You can map these from INSPIRE keywords
image: "{figure_link}"
image_name: "{figure_name}"
arxiv: "{meta.get('arxiv_eprints', [{}])[0].get('value', '')}"
doi: "{meta.get('dois', [{}])[0].get('value', '')}"
citation: {citation_count}
---"""

        with open(f"_publications/{year}-{hit['id']}.md", "w") as f:
            f.write(content)


if __name__ == "__main__":
    update_publications()
