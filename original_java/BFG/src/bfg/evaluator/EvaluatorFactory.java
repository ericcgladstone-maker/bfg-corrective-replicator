package bfg.evaluator;

import java.nio.file.Paths;
import java.util.Properties;

import bfg.misc.Utilities;

public class EvaluatorFactory {
	private static final String PROP_TYPENAME = "evaluator";

	private static final String PROP_FT_CRITERIA = "evaluator.fuzzyterms.criteria";
	private static final String PROP_FT_INDEX = "evaluator.fuzzyterms.index";
	private static final String PROP_FT_EDIT_DISTANCE = "evaluator.fuzzyterms.distance";

	private static final String PROP_REL_CRITERIA = "evaluator.relevancy.criteria";
	private static final String PROP_REL_INDEX = "evaluator.relevancy.index";

	private static final String PROP_WEASEL_TARGET_PREAMBLE = "evaluator.weasel.target";

	public static Evaluator getInstance(Properties props) {
		String type = props.getProperty(PROP_TYPENAME);
		Evaluator evaluator;
		if ("FuzzyTerms".equals(type)) {
			evaluator = new FuzzyTermsEvaluator(ScoringCriteria.valueOf(props.getProperty(PROP_FT_CRITERIA)),
					Paths.get(props.getProperty(PROP_FT_INDEX)),
					Integer.parseInt(props.getProperty(PROP_FT_EDIT_DISTANCE), 10));
		} else if ("Relevancy".equals(type)) {
			evaluator = new RelevancyEvaluator(ScoringCriteria.valueOf(props.getProperty(PROP_REL_CRITERIA)),
					Paths.get(props.getProperty(PROP_REL_INDEX)));
		} else if ("Weasel".equals(type)) {
			evaluator = new WeaselEvaluator(StringSimilarityScorer.getInstance(props),
					Utilities.getInstance().loadStringArray(props, PROP_WEASEL_TARGET_PREAMBLE));
		} else {
			throw new RuntimeException("Unknown evaluator type " + type);
		}
		return evaluator;
	}
}
