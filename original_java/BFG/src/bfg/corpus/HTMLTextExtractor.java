package bfg.corpus;

import org.jsoup.Jsoup;
import org.jsoup.nodes.Document;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class HTMLTextExtractor {
	private static final Logger log = LoggerFactory.getLogger(HTMLTextExtractor.class);

	public static void main(String[] args) {
		String html = "<div><p>Now</p> with <b>bold</b> new <i>flavor.  Welcome to Marlboro Country";
		log.info(new HTMLTextExtractor().extractText(html));
	}

	public String extractText(String html) {
		Document doc = Jsoup.parseBodyFragment(html);
		return doc.body().text();
	}
}
