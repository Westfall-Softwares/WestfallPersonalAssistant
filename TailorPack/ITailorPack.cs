namespace WestfallPersonalAssistant.TailorPack
{
    public interface ITailorPack
    {
        void Initialize();
        void Shutdown();
        TailorPackManifest GetManifest();
        IFeature[] GetFeatures();
    }
}