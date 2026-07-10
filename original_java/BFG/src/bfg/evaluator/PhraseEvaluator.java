package bfg.evaluator;

import java.io.IOException;
import java.nio.file.Path;
import java.util.Arrays;
import java.util.List;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

import org.apache.lucene.index.DirectoryReader;
import org.apache.lucene.index.IndexReader;
import org.apache.lucene.index.Term;
import org.apache.lucene.search.IndexSearcher;
import org.apache.lucene.search.PhraseQuery;
import org.apache.lucene.search.Query;
import org.apache.lucene.search.TopDocs;
import org.apache.lucene.store.FSDirectory;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import bfg.MutationStep;

public class PhraseEvaluator implements Evaluator {
	private static final Logger log = LoggerFactory.getLogger(PhraseEvaluator.class);
	private static final String word_regex = "([a-zA-Z0-9\\-']+)";

	private Path ndxDir;
	private ScoringCriteria scoringCriteria;
	private int slop;

	public PhraseEvaluator(ScoringCriteria scoringCriteria, Path ndxDir, int slop) {
		log.debug("Creating");
		this.ndxDir = ndxDir;
		this.slop = slop;
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
		long start = System.currentTimeMillis();
		try (IndexReader reader = DirectoryReader.open(FSDirectory.open(ndxDir));) {
			// try (IndexReader reader = DirectoryReader.open(new
			// MMapDirectory(ndxDir));) {
			IndexSearcher searcher = new IndexSearcher(reader);
			Arrays.stream(generation).parallel().forEach(x -> evaluate(x, searcher));
		} catch (IOException e) {
			log.error("Unable to apply corrections", e);
		}
		long stop = System.currentTimeMillis();
		log.debug("Evaluation time: {}", stop - start);
		return generation;
	}

	private double evaluate(String str, IndexSearcher searcher) {
		log.trace("Evaluating {}", str);
		double score = 0.0;

		Pattern p = Pattern.compile(word_regex);
		Matcher m = p.matcher(str);
		PhraseQuery.Builder queryBuilder = new PhraseQuery.Builder();
		while (m.find()) {
			String word = m.group();
			queryBuilder.add(new Term("contents", word));
		}
		queryBuilder.setSlop(slop);
		try {
			Query query = queryBuilder.build();
			if (log.isTraceEnabled()) {
				log.trace(query.toString());
			}
			log.debug(query.toString());
			TopDocs results = searcher.search(query, 5);
			score = getScore(results, scoringCriteria);
		} catch (IOException e) {
			log.error("Could not read index {}", str, e);
			throw new RuntimeException(e);
		}
		log.trace("Evaluated {} ::: {}", str, score);
		return score;
	}

	@Override
	public String description() {
		return "PhraseEvaluator [ndxDir=" + ndxDir + ", scoringCriteria=" + scoringCriteria + ", slop=" + slop + "]";
	}

}
