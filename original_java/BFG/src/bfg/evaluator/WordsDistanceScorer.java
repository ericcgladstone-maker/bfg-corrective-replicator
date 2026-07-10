package bfg.evaluator;

import java.util.ArrayList;
import java.util.List;

import com.google.common.base.CharMatcher;
import com.google.common.base.Splitter;

public class WordsDistanceScorer implements StringSimilarityScorer {
	private static final Splitter wordSplitter = Splitter.on(CharMatcher.anyOf(" :-'\",;.?")).omitEmptyStrings()
			.trimResults();

	@Override
	public double similarity(String str1, String str2) {
		List<String> wl1 = new ArrayList<>(getWordList(str1));
		List<String> wl2 = new ArrayList<>(getWordList(str2));
		List<String> longList;
		List<String> shortList;
		if (wl1.size() > wl2.size()) {
			longList = wl1;
			shortList = wl2;
		} else {
			longList = wl1;
			shortList = wl2;
		}
		int longLength = longList.size();
		// don't use removeAll() to handle possible duplicates in longList
		for (String word : shortList) {
			longList.remove(word);
		}
		return ((double) (longLength - longList.size())) / longLength;
	}

	private List<String> getWordList(String line) {
		return wordSplitter.splitToList(line);
	}

	@Override
	public String description() {
		return "Word Containment Scorer";
	}

}
