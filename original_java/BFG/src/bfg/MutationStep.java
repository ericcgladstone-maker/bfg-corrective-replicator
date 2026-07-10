package bfg;

import java.util.Map;
import java.util.TreeMap;
import java.util.UUID;

import com.google.common.base.MoreObjects;

public class MutationStep {
	private final UUID id = UUID.randomUUID();
	private final UUID parentId;
	private String childString;
	private String parentString;
	private String survivalTarget;
	private Map<String, Double> fitnessScores = new TreeMap<>();

	public MutationStep() {
		parentId = null;
	}

	public MutationStep(MutationStep step) {
		parentString = step.getChildString();
		parentId = step.getId();
	}

	public String getChildString() {
		return childString;
	}

	public double getFitnessScore(String targetString) {
		return fitnessScores.getOrDefault(targetString, Double.valueOf(0.0d));
	}

	public String getParentString() {
		return parentString;
	}

	public void setChildString(String childString) {
		this.childString = childString;
	}

	public void setFitnessScore(String targetString, double fitnessScore) {
		this.fitnessScores.put(targetString, Double.valueOf(fitnessScore));
	}

	public void setParentString(String parentString) {
		this.parentString = parentString;
	}

	public String getConvergingToString() {
		return fitnessScores.entrySet().stream().max(Map.Entry.comparingByValue(Double::compare))
				.orElse(Map.entry("", Double.valueOf(0.0d))).getKey();
	}

	public double getConvergingToFitness() {
		return getFitnessScore(getConvergingToString());
	}

	public String getSurvivalTarget() {
		return MoreObjects.firstNonNull(survivalTarget, getConvergingToString());
	}

	public void setSurvivalTarget(String survivalTarget) {
		this.survivalTarget = survivalTarget;
	}

	public double getSurvivalTargetFitness() {
		return getFitnessScore(getSurvivalTarget());
	}

	public UUID getId() {
		return id;
	}

	public UUID getParentId() {
		return parentId;
	}

}
