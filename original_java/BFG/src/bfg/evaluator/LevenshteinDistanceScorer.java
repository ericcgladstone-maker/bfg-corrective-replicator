package bfg.evaluator;

import org.apache.commons.text.similarity.LevenshteinDistance;

public class LevenshteinDistanceScorer implements StringSimilarityScorer {
	private LevenshteinDistance ld;

	public LevenshteinDistanceScorer() {
		ld = new LevenshteinDistance();
	}

	@Override
	public double similarity(String str1, String str2) {
		int maxLength = Math.max(str1.length(), str2.length());
		return ((double) (maxLength - ld.apply(str1, str2))) / maxLength;
	}

	@Override
	public String description() {
		return "Levenshtein Edit Distance Scorer";
	}

}
