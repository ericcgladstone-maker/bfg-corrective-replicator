package bfg.recorder;

public class SummaryRecord {
	/**
	 * The number of the generation; # in the generation.# filename.
	 */
	private int generation;
	/**
	 * The position of this element in the generation. Elements are sorted based on
	 * "fitness_score".
	 */
	private int rank;
	/** The element's string as mutated from "parent_text". */
	private String text;
	/**
	 * The string in the prior generation that was the basis for the mutation.
	 */
	private String parentText;
	/**
	 * The sentence in the configured targets which is most like the current "text"
	 * value based on "fitness_score".
	 */
	private String targetText;
	/**
	 * Numerical evaluation of "text" compared to "target_text". The range varies by
	 * the evaluator type, but for the Weasel evaluator it is between 0 and 1.
	 */
	private double fitnessScore;
	/**
	 * Number of elements in the generation. After the initial population growth
	 * this will be the same as the configured reaper's maxelements value.
	 */
	private int numberInGeneration;
	/**
	 * Value of "fitness_score" above which "text" is considered to behave achieved
	 * full fitness as specified in the run configuration file.
	 */
	private double fullFitnessScore;
	/**
	 * Number of elements in the current generation whose"fitness_score" is greater
	 * than "full_fitness_score"
	 */
	private double numberFullFitness;

	public SummaryRecord() {
	}

	public int getGeneration() {
		return generation;
	}

	public void setGeneration(int generation) {
		this.generation = generation;
	}

	public int getRank() {
		return rank;
	}

	public void setRank(int rank) {
		this.rank = rank;
	}

	public String getText() {
		return text;
	}

	public void setText(String text) {
		this.text = text;
	}

	public String getParentText() {
		return parentText;
	}

	public void setParentText(String parentText) {
		this.parentText = parentText;
	}

	public String getTargetText() {
		return targetText;
	}

	public void setTargetText(String targetText) {
		this.targetText = targetText;
	}

	public double getFitnessScore() {
		return fitnessScore;
	}

	public void setFitnessScore(double fitnessScore) {
		this.fitnessScore = fitnessScore;
	}

	public int getNumberInGeneration() {
		return numberInGeneration;
	}

	public void setNumberInGeneration(int numberInGeneration) {
		this.numberInGeneration = numberInGeneration;
	}

	public double getFullFitnessScore() {
		return fullFitnessScore;
	}

	public void setFullFitnessScore(double fullFitnessScore) {
		this.fullFitnessScore = fullFitnessScore;
	}

	public double getNumberFullFitness() {
		return numberFullFitness;
	}

	public void setNumberFullFitness(double numberFullFitness) {
		this.numberFullFitness = numberFullFitness;
	}

}
