package bfg.corrector;

public class CompoundCorrectorStep {
	private final Corrector corrector;
	private final double weight;

	public CompoundCorrectorStep(Corrector corrector, double weight) {
		this.corrector = corrector;
		this.weight = weight;
	}

	public Corrector getCorrector() {
		return corrector;
	}

	public double getWeight() {
		return weight;
	}

}
