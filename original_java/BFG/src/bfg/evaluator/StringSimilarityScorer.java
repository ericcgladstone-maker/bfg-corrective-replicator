package bfg.evaluator;

import java.util.Properties;

import bfg.Describable;

public interface StringSimilarityScorer extends Describable {
	static final String PROP_WEASEL_SIMILARITY = "evaluator.weasel.similarity";
	static final String PROP_SIMLIARITY_WNL_L_WGT = "evaluator.weasel.similarity.words_n_levenshtein.levenshteinWeight";
	static final String PROP_SIMLIARITY_WNL_W_WGT = "evaluator.weasel.similarity.words_n_levenshtein.wordWeight";

	public double similarity(String str1, String str2);

	public static StringSimilarityScorer getInstance(Properties props) {
		StringSimilarity similarity = StringSimilarity.valueOf(props.getProperty(PROP_WEASEL_SIMILARITY));
		switch (similarity) {
		case LEVENSHTEIN:
			return new LevenshteinDistanceScorer();
		case WORDS:
			return new WordsDistanceScorer();
		case WORDS_N_LEVENSHTEIN:
			return new CompoundDistanceScorer( //
					new CompoundDistanceScorerStep(new WordsDistanceScorer(),
							Double.parseDouble(props.getProperty(PROP_SIMLIARITY_WNL_W_WGT, "1.0"))), //
					new CompoundDistanceScorerStep(new LevenshteinDistanceScorer(),
							Double.parseDouble(props.getProperty(PROP_SIMLIARITY_WNL_L_WGT, "1.0"))) //
			);
		default:
			throw new IllegalArgumentException("Unhandled StringSimlarity " + similarity);
		}
	}
}
