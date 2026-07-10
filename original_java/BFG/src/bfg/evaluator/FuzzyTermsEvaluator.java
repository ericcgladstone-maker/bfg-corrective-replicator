package bfg.evaluator;

import java.io.IOException;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.concurrent.Callable;
import java.util.concurrent.ExecutionException;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

import org.apache.lucene.analysis.standard.StandardAnalyzer;
import org.apache.lucene.index.DirectoryReader;
import org.apache.lucene.index.IndexReader;
import org.apache.lucene.index.Term;
import org.apache.lucene.queryparser.classic.ParseException;
import org.apache.lucene.queryparser.classic.QueryParser;
import org.apache.lucene.search.FuzzyQuery;
import org.apache.lucene.search.IndexSearcher;
import org.apache.lucene.search.MultiPhraseQuery;
import org.apache.lucene.search.Query;
import org.apache.lucene.search.TopDocs;
import org.apache.lucene.search.spans.SpanMultiTermQueryWrapper;
import org.apache.lucene.search.spans.SpanOrQuery;
import org.apache.lucene.store.FSDirectory;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.google.common.cache.Cache;
import com.google.common.cache.CacheBuilder;

import bfg.MutationStep;

public class FuzzyTermsEvaluator implements Evaluator {
	private static final Logger log = LoggerFactory.getLogger(FuzzyTermsEvaluator.class);
	private static final String word_regex = "([a-zA-Z0-9\\-']+)";

	private int maxDistance;
	private Path ndxDir;
	private ScoringCriteria scoringCriteria;

	private Cache<String, Double> scoreCache = CacheBuilder.newBuilder().maximumSize(10000).recordStats().build();

	public FuzzyTermsEvaluator(ScoringCriteria scoringCriteria, Path ndxDir, int maxDistance) {
		log.debug("Creating");
		this.ndxDir = ndxDir;
		this.maxDistance = maxDistance;
		this.scoringCriteria = scoringCriteria;
	}

	@Override
	public List<MutationStep> evaluate(List<MutationStep> generationList) {
		return Arrays.asList(evaluate(generationList.toArray(new MutationStep[0])));
	}

	private MutationStep evaluate(MutationStep step, IndexSearcher searcher) {
		String childString = step.getChildString();
		double evalScore;
		try {
			evalScore = scoreCache.get(childString, new Callable<Double>() {
				@Override
				public Double call() throws Exception {
					return evaluate_parsed(childString, searcher);
				}
			});
		} catch (ExecutionException e) {
			log.error("Unable to evaluate {}", childString, e);
			evalScore = 0.0;
		}
		step.setFitnessScore("", evalScore);
		return step;
	}

	public MutationStep[] evaluate(MutationStep[] generation) {
		long start = System.currentTimeMillis();
		scoreCache.cleanUp();
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

	private double evaluate_multiphrase(String str, IndexSearcher searcher) {
		double score = 0.0;

		Pattern p = Pattern.compile(word_regex);
		Matcher m = p.matcher(str.toLowerCase());
		MultiPhraseQuery.Builder queryBuilder = new MultiPhraseQuery.Builder();
		while (m.find()) {
			String word = m.group();
			queryBuilder.add(new Term[] { new Term("contents", word), new Term("contents", word + "s") });
			FuzzyQuery q = new FuzzyQuery(new Term("contents", word + "~" + maxDistance));

		}
		try {
			// Query query = new SpanNearQuery(queryTerms.toArray(new
			// SpanMultiTermQueryWrapper[0]), 0, true);
			Query query = queryBuilder.build();
			if (log.isTraceEnabled()) {
				log.trace(query.rewrite(searcher.getIndexReader()).toString());
			}
			TopDocs results = searcher.search(query, 5);
			score = getScore(results, scoringCriteria);
		} catch (IOException e) {
			log.error("Could not read index {}", str, e);
			throw new RuntimeException(e);
		}
		return score;
	}

	private double evaluate_parsed(String str, IndexSearcher searcher) {
		double score = 0.0;

		Pattern p = Pattern.compile(word_regex);
		Matcher m = p.matcher(str.toLowerCase());
		StringBuffer querySB = new StringBuffer();
		while (m.find()) {
			String word = m.group();
			querySB.append(word).append('~').append(maxDistance).append(' ');
		}
		String queryStr = querySB.toString().trim();
		QueryParser parser = new QueryParser("contents", new StandardAnalyzer());
		try {
			Query query = parser.parse(queryStr);
			if (log.isTraceEnabled()) {
				log.trace(query.toString());
			}
			TopDocs results = searcher.search(query, 5);
			score = getScore(results, scoringCriteria);
		} catch (ParseException e) {
			log.error("Could not parse {}", str, e);
			throw new RuntimeException(e);
		} catch (IOException e) {
			log.error("Could not read index {}", str, e);
			throw new RuntimeException(e);
		}
		return score;
	}

	private double evaluate_span(String str, IndexSearcher searcher) {
		double score = 0.0;

		Pattern p = Pattern.compile(word_regex);
		Matcher m = p.matcher(str.toLowerCase());
		ArrayList<SpanMultiTermQueryWrapper<FuzzyQuery>> queryTerms = new ArrayList<>();
		while (m.find()) {
			String word = m.group();
			queryTerms.add(
					new SpanMultiTermQueryWrapper<>(new FuzzyQuery(new Term("contents", word + "~" + maxDistance))));
		}
		try {
			// Query query = new SpanNearQuery(queryTerms.toArray(new
			// SpanMultiTermQueryWrapper[0]), 0, true);
			Query query = new SpanOrQuery(queryTerms.toArray(new SpanMultiTermQueryWrapper[0]));
			if (log.isTraceEnabled()) {
				log.trace(query.rewrite(searcher.getIndexReader()).toString());
			}
			TopDocs results = searcher.search(query, 5);
			score = getScore(results, scoringCriteria);
		} catch (IOException e) {
			log.error("Could not read index {}", str, e);
			throw new RuntimeException(e);
		}
		return score;
	}

	@Override
	public String description() {
		return "FuzzyTermsEvaluator [maxDistance=" + maxDistance + ", ndxDir=" + ndxDir + ", scoringCriteria="
				+ scoringCriteria + "]";
	}

}
