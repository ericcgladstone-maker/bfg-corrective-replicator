package bfg.test;

import java.io.FileInputStream;
import java.io.IOException;
import java.nio.file.Paths;

import org.apache.lucene.index.IndexWriterConfig;
import org.apache.lucene.search.spell.PlainTextDictionary;
import org.apache.lucene.search.spell.SpellChecker;
import org.apache.lucene.search.spell.StringDistance;
import org.apache.lucene.store.Directory;
import org.apache.lucene.store.FSDirectory;

public class SpellcheckerTest {

	public static void main(String[] args) throws IOException {
		// Directory dictionaryDirectory = new RAMDirectory();
		// Directory dictionaryDirectory = new
		// WindowsDirectory(Paths.get("spellNdx"));
		Directory dictionaryDirectory = FSDirectory.open(Paths.get("spellNdx"));
		try (SpellChecker spell = new SpellChecker(dictionaryDirectory)) {
			spell.indexDictionary(new PlainTextDictionary(new FileInputStream("en-US.dic")), new IndexWriterConfig(),
					false);
			String findWord = "frefedom";
			if (spell.exist(findWord)) {
				System.out.println(findWord + " exists");
			} else {
				System.out.println(findWord + " not found.  Suggestions:");
				String[] suggestions = spell.suggestSimilar(findWord, 5);
				StringDistance wordDiff = spell.getStringDistance();
				for (String suggestion : suggestions) {
					System.out.println(suggestion + " " + wordDiff.getDistance(findWord, suggestion));
				}
			}
		}
	}

}
