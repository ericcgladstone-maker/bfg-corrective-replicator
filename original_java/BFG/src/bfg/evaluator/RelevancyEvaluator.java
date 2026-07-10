package bfg.evaluator;

import java.io.IOException;
import java.nio.file.Path;
import java.util.Arrays;
import java.util.List;

import org.apache.lucene.analysis.Analyzer;
import org.apache.lucene.analysis.standard.StandardAnalyzer;
import org.apache.lucene.index.DirectoryReader;
import org.apache.lucene.index.IndexReader;
import org.apache.lucene.queryparser.classic.ParseException;
import org.apache.lucene.queryparser.classic.QueryParser;
import org.apache.lucene.search.IndexSearcher;
import org.apache.lucene.search.Query;
import org.apache.lucene.search.TopDocs;
import org.apache.lucene.store.MMapDirectory;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import bfg.MutationStep;

public class RelevancyEvaluator implements Evaluator {
	private static final Logger log = LoggerFactory.getLogger(RelevancyEvaluator.class);

	private Path ndxDir;
	private ScoringCriteria scoringCriteria;

	public RelevancyEvaluator(ScoringCriteria scoringCriteria, Path ndxDir) {
		log.debug("Creating");
		this.ndxDir = ndxDir;
		this.scoringCriteria = scoringCriteria;
	}

	@Override
	public List<MutationStep> evaluate(List<MutationStep> generationList) {
		return Arrays.asList(evaluate(generationList.toArray(new MutationStep[0])));
	}

	private MutationStep evaluate(MutationStep step, IndexSearcher searcher) {
		step.setFitnessScore("", evaluate(step.getChildString(), searcher));
		return step;
	}

	public MutationStep[] evaluate(MutationStep[] generation) {
		printHead(generation);
		long start = System.currentTimeMillis();
		// try (IndexReader reader =
		// DirectoryReader.open(FSDirectory.open(ndxDir));) {
		try (IndexReader reader = DirectoryReader.open(new MMapDirectory(ndxDir));) {
			IndexSearcher searcher = new IndexSearcher(reader);
			Arrays.stream(generation).parallel().forEach(x -> evaluate(x, searcher));
		} catch (IOException e) {
			log.error("Unable to apply corrections", e);
		}
		long stop = System.currentTimeMillis();
		printHead(generation);
		log.debug("Evaluation time: {}", stop - start);
		return generation;
	}

	private double evaluate(String str, IndexSearcher searcher) {
		double score = 0.0;
		Analyzer analyzer = new StandardAnalyzer();
		QueryParser parser = new QueryParser("contents", analyzer);

		try {
			Query query = parser.parse(str);
			TopDocs results = searcher.search(query, 5);
			score = getScore(results, scoringCriteria);
		} catch (ParseException e) {
			log.error("Could not parse {}", str, e);
			throw new RuntimeException(e);
		} catch (IOException e) {
			log.error("Could not read index {}", str, e);
			throw new RuntimeException(e);
		}
		if (Double.isNaN(score)) {
			score = 0.0;
		}
		return score;
	}

	private void printHead(MutationStep[] generation) {
		for (int i = 0; i < Math.min(generation.length, 10); i++) {
			log.trace("Fitness score {}", generation[i].getConvergingToFitness());
		}
	}

	@Override
	public String description() {
		return "RelevancyEvaluator [ndxDir=" + ndxDir + ", scoringCriteria=" + scoringCriteria + "]";
	}

}
