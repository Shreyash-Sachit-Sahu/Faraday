import SiteNav from "@/components/SiteNav";
import Hero from "@/components/Hero";
import FeatureSection from "@/components/FeatureSection";
import ClosingCTA from "@/components/ClosingCTA";
import SiteFooter from "@/components/SiteFooter";
import {
  ShowsWorkVisual,
  FieldVisual,
  NotesVisual,
  PlainVisual,
} from "@/components/Visuals";

export default function Home() {
  return (
    <main>
      <SiteNav />
      <Hero />

      <div id="features" className="mx-auto max-w-[1100px] space-y-28 px-6 py-28 md:py-36">
        <FeatureSection
          index="01"
          title="It shows its work."
          body="Every answer cites the passages it drew from, so you can trust it, check it, and read further. No black boxes."
          visual={<ShowsWorkVisual />}
        />
        <FeatureSection
          index="02"
          title="It studied the whole field."
          body="Tens of thousands of passages across algorithms, systems, networks, and theory — retrieved and re-ranked for your exact question, not keyword-matched."
          visual={<FieldVisual />}
          reverse
        />
        <FeatureSection
          index="03"
          title="It reads your notes, too."
          body="Drop in a lecture slide deck or a textbook chapter. Faraday folds it into its answers — visible only in your account, never anyone else's."
          visual={<NotesVisual />}
        />
        <FeatureSection
          index="04"
          title="It speaks plainly."
          body="Tuned to explain like a great teaching assistant — direct, concrete, and showing code exactly when code makes it clearer."
          visual={<PlainVisual />}
          reverse
        />
      </div>

      <ClosingCTA />
      <SiteFooter />
    </main>
  );
}
