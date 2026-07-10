package bfg.evaluator;

import java.util.Arrays;
import java.util.List;

import org.apache.lucene.search.TopDocs;

import bfg.Describable;
import bfg.MutationStep;

public interface Evaluator extends Describable {

	default double getScore(TopDocs results, ScoringCriteria scoringCriteria) {
		if (ScoringCriteria.BEST_SCORE.equals(scoringCriteria)) {
			return Arrays.stream(results.scoreDocs).mapToDouble(sd -> sd.score).summaryStatistics().getMax();
		} else {
			return results.totalHits.value;
		}
	}

	List<MutationStep> evaluate(List<MutationStep> generationList);

}
