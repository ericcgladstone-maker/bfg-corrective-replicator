package bfg.test;

import bfg.evaluator.CompoundDistanceScorer;
import bfg.evaluator.CompoundDistanceScorerStep;
import bfg.evaluator.LevenshteinDistanceScorer;
import bfg.evaluator.StringSimilarityScorer;
import bfg.evaluator.WordsDistanceScorer;

public class DistanceScorerTest {

	public static void main(String[] args) {
		StringSimilarityScorer s;
		String[][] testStrings = { //
				{ //
						"Next, he's the governor of this country, and a man whom I am bound to.", //
						"Next, he's the governor of this country, and a man whom I am bound to." //
				}, //
				{ //
						"My lord, you must tell us where the body is, and go with us to the king.", //
						"My lord, you must tell us where the body is, and go with us to the king.".toLowerCase() } //
		};//
		System.out.println("Testing Levenshtein Distance Scorer");
		s = new LevenshteinDistanceScorer();
		for (String[] ts : testStrings) {
			System.out.printf("Comparing%n%s%nto%n%s%nScore: %f%n%n", ts[0], ts[1], s.similarity(ts[0], ts[1]));
		}
		System.out.println("Testing Words and Levenshtein Distance Scorer");
		s = new CompoundDistanceScorer( //
				new CompoundDistanceScorerStep(new WordsDistanceScorer(), 3.0), //
				new CompoundDistanceScorerStep(new LevenshteinDistanceScorer(), 1.0) //
		);
		for (String[] ts : testStrings) {
			System.out.printf("Comparing%n%s%nto%n%s%nScore: %f%n%n", ts[0], ts[1], s.similarity(ts[0], ts[1]));
		}
	}

}
